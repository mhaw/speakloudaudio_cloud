import logging
import os  # Fix: Import os for file operations
from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash
from app.firestore_database_operations import (
    save_article_metadata,
    get_all_articles,
    get_recent_articles,
    get_article_by_id,
    update_article,
    get_articles_by_hashtag,
    delete_article_by_id,
)
from app.firestore_utils import log_listen_event
from app.services import validate_url  # Fix: Import validate_url
from app.text_extraction import extract_text_from_url  # Fix: Import extract_text_from_url
from app.file_management import generate_audio_file_path  # Fix: Import generate_audio_file_path
from app.text_to_speech_service import text_to_speech  # Fix: Import text_to_speech
from app.cloud_storage import upload_to_gcs  # Fix: Import upload_to_gcs

# Configure logging
logging.basicConfig(level=logging.INFO)

# Define the Blueprint
main = Blueprint("main", __name__)

# Routes
@main.route("/")
def index():
    """Home page that displays recent articles."""
    try:
        recent_articles = get_recent_articles(limit=5)
        logging.info("Index page loaded successfully with recent articles.")
        return render_template("index.html", recent_articles=recent_articles)
    except Exception as e:
        logging.error(f"Error loading the index page: {e}", exc_info=True)
        flash("An error occurred while loading the page.", "error")
        return redirect(url_for("main.index"))


@main.route("/processed_articles", methods=["GET"])
def processed_articles():
    """Displays all processed articles with sorting, filtering, and pagination."""
    try:
        page = request.args.get("page", 1, type=int)
        per_page = 10
        sort_by = request.args.get("sort_by", "processed_date")
        order = request.args.get("order", "desc")

        # Fetch articles and sort
        all_articles = get_all_articles()
        reverse = order == "desc"
        sorted_articles = sorted(
            all_articles,
            key=lambda x: x.get(sort_by, ""),
            reverse=reverse,
        )

        # Paginate articles
        total_articles = len(sorted_articles)
        total_pages = (total_articles + per_page - 1) // per_page
        start = (page - 1) * per_page
        paginated_articles = sorted_articles[start:start + per_page]

        logging.info(f"Processed articles loaded successfully. Page: {page}, Total Pages: {total_pages}")
        return render_template(
            "processed_articles.html",
            articles=paginated_articles,
            page=page,
            total_pages=total_pages,
            sort_by=sort_by,
            order=order,
        )
    except Exception as e:
        logging.error(f"Error loading processed articles: {e}", exc_info=True)
        flash("An error occurred while loading the articles.", "error")
        return redirect(url_for("main.index"))


@main.route("/article/<string:article_id>")
def article_detail(article_id):
    """Displays details of a single article."""
    try:
        article = get_article_by_id(article_id)
        if not article:
            logging.warning(f"Article with ID {article_id} not found.")
            flash("Article not found.", "error")
            return redirect(url_for("main.processed_articles"))
        logging.info(f"Article details loaded for ID: {article_id}")
        return render_template("article_detail.html", article=article)
    except Exception as e:
        logging.error(f"Error loading article details for ID {article_id}: {e}", exc_info=True)
        flash("An error occurred while loading the article details.", "error")
        return redirect(url_for("main.processed_articles"))


@main.route("/delete_article/<string:article_id>", methods=["POST"])
def delete_article(article_id):
    """Deletes an article by ID."""
    try:
        delete_article_by_id(article_id)
        logging.info(f"Article with ID {article_id} deleted successfully.")
        flash("Article deleted successfully.", "success")
        return redirect(url_for("main.processed_articles"))
    except Exception as e:
        logging.error(f"Error deleting article with ID {article_id}: {e}", exc_info=True)
        flash("An error occurred while deleting the article.", "error")
        return redirect(url_for("main.processed_articles"))


@main.route("/search_by_hashtag", methods=["GET"])
def search_by_hashtag():
    """Searches for articles by a specific hashtag."""
    hashtag = request.args.get("hashtag", "").strip()
    if not hashtag:
        flash("No hashtag provided.", "error")
        return redirect(url_for("main.processed_articles"))
    try:
        articles = get_articles_by_hashtag(hashtag)
        logging.info(f"Articles loaded successfully for hashtag: #{hashtag}")
        return render_template(
            "processed_articles.html",
            articles=articles,
            page=1,
            total_pages=1,
            sort_by=None,
            order=None,
        )
    except Exception as e:
        logging.error(f"Error searching for articles with hashtag #{hashtag}: {e}", exc_info=True)
        flash("An error occurred while searching for articles.", "error")
        return redirect(url_for("main.processed_articles"))


@main.route("/update_article/<string:article_id>", methods=["POST"])
def update_article_tags(article_id):
    """Updates hashtags for an article."""
    new_hashtags = request.form.get("hashtags", "").split(",")
    try:
        update_article(
            article_id,
            {"hashtags": [tag.strip() for tag in new_hashtags if tag.strip()]},
        )
        logging.info(f"Article hashtags updated successfully for ID: {article_id}")
        flash("Article hashtags updated successfully.", "success")
        return redirect(url_for("main.article_detail", article_id=article_id))
    except Exception as e:
        logging.error(f"Error updating hashtags for article ID {article_id}: {e}", exc_info=True)
        flash("An error occurred while updating the hashtags.", "error")
        return redirect(url_for("main.article_detail", article_id=article_id))


@main.route("/process_article", methods=["POST"])
def process_article():
    """Processes an article and generates audio."""
    try:
        url = request.form.get("url", "").strip()
        hashtags = request.form.get("hashtags", "").strip().split(",")

        logging.info(f"Processing article with URL: {url} and hashtags: {hashtags}")

        # Validate URL
        if not validate_url(url):
            flash("Invalid URL. Please check the URL format and try again.", "error")
            return redirect(url_for("main.index"))

        # Extract article data
        article_data = extract_text_from_url(url)
        if not article_data.get("text"):
            flash("Failed to extract text from the article.", "error")
            return redirect(url_for("main.index"))

        # Generate audio file path
        output_file = generate_audio_file_path(article_data, "downloads")

        # Convert text to audio
        text_to_speech(article_data["text"], output_file, article_data)

        # Upload to Google Cloud Storage
        download_link = upload_to_gcs(output_file, os.path.basename(output_file))

        # Save metadata
        save_article_metadata(
            title=article_data["title"],
            source=article_data["source"],
            url=url,
            publish_date=article_data["publish_date"],
            download_link=download_link,
            authors=article_data["authors"],
            text_content=article_data["text"],
            hashtags=[tag.strip() for tag in hashtags if tag.strip()],
        )

        flash("Article processed successfully.", "success")
        return redirect(url_for("main.index"))

    except Exception as e:
        logging.error(f"Error processing article: {e}", exc_info=True)
        flash("An unexpected error occurred while processing the article.", "error")
        return redirect(url_for("main.index"))
