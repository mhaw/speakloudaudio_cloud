import datetime
import logging
import time
from newspaper import Article, Config
from bs4 import BeautifulSoup
from typing import Dict, Any
import requests
from requests.exceptions import HTTPError, RequestException

# Custom User-Agent header to avoid bot detection
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Referer": "https://www.google.com/",
    "Accept-Language": "en-US,en;q=0.9",
}

def extract_text_from_url(url: str, retries: int = 3, backoff_factor: int = 2) -> Dict[str, Any]:
    """
    Extracts article text, title, author info, and publish date from the provided URL.
    Tries newspaper3k first, then falls back to BeautifulSoup + meta tags.
    """
    article_data = {
        "title": "Unknown Title",
        "text": "",
        "authors": ["Unknown Author"],
        "publish_date": "Unknown Date",
        "source": url
    }

    for attempt in range(retries):
        try:
            config = Config()
            config.browser_user_agent = HEADERS["User-Agent"]
            config.request_timeout = 15

            article = Article(url, config=config)
            article.download()
            article.parse()

            article_data["title"] = article.title or article_data["title"]
            article_data["text"] = article.text or article_data["text"]
            article_data["authors"] = article.authors or article_data["authors"]
            if article.publish_date:
                article_data["publish_date"] = article.publish_date.strftime("%Y-%m-%d")

            logging.info(f"Successfully extracted article data from URL: {url}")
            return article_data

        except HTTPError as http_err:
            logging.warning(f"HTTP error on attempt {attempt + 1}/{retries} for {url}: {http_err}")
        except RequestException as req_err:
            logging.warning(f"Request error on attempt {attempt + 1}/{retries} for {url}: {req_err}")
        except Exception as e:
            logging.error(f"Unexpected error on attempt {attempt + 1}/{retries} for {url}: {e}")

        time.sleep(backoff_factor ** attempt)

    # Fallback extraction using requests + BeautifulSoup
    try:
        logging.info(f"Fallback extraction using BeautifulSoup for URL: {url}")
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        # Title
        if soup.title:
            article_data["title"] = soup.title.string.strip()

        # Text
        paragraphs = soup.find_all('p')
        if paragraphs:
            article_data["text"] = " ".join(p.get_text().strip() for p in paragraphs if p.get_text().strip())

        # Metadata from OpenGraph, Twitter, or article meta tags
        meta_title = soup.find("meta", property="og:title") or soup.find("meta", attrs={"name": "twitter:title"})
        if meta_title and meta_title.get("content"):
            article_data["title"] = meta_title["content"]

        meta_author = soup.find("meta", attrs={"name": "author"})
        if meta_author and meta_author.get("content"):
            article_data["authors"] = [meta_author["content"]]

        meta_date = soup.find("meta", property="article:published_time") or soup.find("meta", attrs={"name": "date"})
        if meta_date and meta_date.get("content"):
            try:
                article_data["publish_date"] = datetime.datetime.fromisoformat(meta_date["content"]).strftime("%Y-%m-%d")
            except Exception as e:
                logging.warning(f"Could not parse publish date: {e}")

        logging.info(f"Fallback extraction successful for URL: {url}")

    except Exception as e:
        logging.error(f"Fallback extraction failed for URL {url}: {e}")

    return article_data
