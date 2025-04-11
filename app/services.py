import logging
import traceback
import os
from urllib.parse import urlparse
from flask import render_template, request, redirect, url_for, flash
from app.firestore_database_operations import (
    get_all_articles,
    save_article_metadata,
    get_article_by_url,
)
from app.firestore_utils import log_listen_event
from .text_extraction import extract_text_from_url
from .text_to_speech_service import text_to_speech
from .cloud_storage import upload_to_gcs
from .file_management import (
    generate_audio_file_path,
    create_directory_if_not_exists,
    extract_metadata,
)

def get_paginated_articles(page: int = 1, per_page: int = 10):
    try:
        all_articles = get_all_articles()
        total_articles = len(all_articles)
        total_pages = (total_articles + per_page - 1) // per_page
        start = (page - 1) * per_page
        end = start + per_page
        paginated_articles = all_articles[start:end]

        articles_with_listens = [
            {
                "id": article.get("id"),
                "title": article.get("title", "Unknown Title"),
                "source": article.get("source", "Unknown Source"),
                "url": article.get("url", "#"),
                "publish_date": article.get("publish_date", "Unknown Date"),
                "processed_date": article.get("processed_date", "Unknown Date"),
                "download_link": article.get("download_link", "#"),
                "authors": article.get("authors", "Unknown Author"),
                "hashtags": article.get("hashtags", []),
                "voice_name": article.get("voice_name", "Default"),
                "audio_length": article.get("audio_length"),
                "listen_count": log_listen_event(article.get("id", ""), count_only=True) if article.get("id") else 0,
            }
            for article in paginated_articles
        ]

        return {
            "articles": articles_with_listens,
            "page": page,
            "total_pages": total_pages,
        }
    except Exception as e:
        logging.error(f"Error loading processed articles: {e}")
        return None

def process_article(url: str, hashtags: list = None, voice_name: str = None) -> str:
    try:
        logging.info(f"Processing article for URL: {url}")

        if not validate_url(url):
            raise ValueError(f"Invalid URL: {url}")

        existing_article = get_article_by_url(url)
        if existing_article:
            logging.info(f"Article already processed: {url}")
            return existing_article["download_link"]

        article_data = extract_text_from_url(url)
        if not article_data.get("text"):
            raise ValueError("No text content found at the provided URL.")

        downloads_directory = "downloads"
        create_directory_if_not_exists(downloads_directory)
        audio_file_path = generate_audio_file_path(article_data, downloads_directory)

        logging.info("Converting text to audio.")
        audio_length = text_to_speech(
            article_data["text"],
            audio_file_path,
            metadata=article_data,
            voice_name=voice_name
        )

        logging.info(f"Uploading {audio_file_path} to Google Cloud Storage.")
        download_link = upload_to_gcs(audio_file_path, os.path.basename(audio_file_path))

        logging.info("Saving metadata to Firestore.")
        metadata = extract_metadata(article_data)
        save_article_metadata(
            title=metadata["title"],
            source=metadata["source"],
            url=url,
            publish_date=metadata["publish_date"],
            download_link=download_link,
            authors=metadata["authors"],
            text_content=article_data["text"],
            hashtags=hashtags or [],
            voice_name=voice_name,
            audio_length=round(audio_length, 2)
        )

        return download_link
    except Exception as e:
        logging.error(f"Error processing article: {e}")
        logging.error(traceback.format_exc())
        raise

def process_multiple_articles(urls: list, hashtags: list = None, voice_name: str = None) -> list:
    results = []
    for url in urls:
        if not validate_url(url):
            logging.warning(f"Invalid URL skipped: {url}")
            results.append({"url": url, "status": "Failed", "error": "Invalid URL"})
            continue

        try:
            download_link = process_article(url, hashtags=hashtags, voice_name=voice_name)
            results.append({"url": url, "status": "Success", "download_link": download_link})
        except Exception as e:
            logging.error(f"Failed to process {url}: {e}")
            results.append({"url": url, "status": "Failed", "error": str(e)})
    return results

def validate_url(url: str) -> bool:
    parsed_url = urlparse(url)
    is_valid = bool(parsed_url.scheme and parsed_url.netloc)
    if not is_valid:
        logging.warning(f"Invalid URL provided: {url}")
    return is_valid

def preview_article_metadata(url: str) -> dict:
    try:
        logging.info(f"Previewing metadata for URL: {url}")

        if not validate_url(url):
            raise ValueError(f"Invalid URL: {url}")

        article_data = extract_text_from_url(url)
        if not article_data.get("text"):
            raise ValueError("No text content found at the provided URL.")

        metadata = extract_metadata(article_data)
        return {
            "title": metadata.get("title", "Unknown Title"),
            "source": metadata.get("source", "Unknown Source"),
            "publish_date": metadata.get("publish_date", "Unknown Date"),
            "authors": metadata.get("authors", "Unknown Author"),
        }
    except Exception as e:
        logging.error(f"Error previewing article metadata: {e}")
        raise
