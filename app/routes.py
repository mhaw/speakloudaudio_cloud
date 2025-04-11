import logging
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
from app.file_management import generate_audio_file_path
from app.text_extraction import extract_text_from_url
from app.text_to_speech_service import text_to_speech
from app.cloud_storage import upload_to_gcs

main = Blueprint("main", __name__)

@main.route("/")
def index():
    try:
        recent_articles = get_recent_articles(limit=5)
        return render_template("index.html", recent_articles=recent_articles)
    except Exception as e:
        logging.error(f"Error loading index: {e}")
        flash("An error occurred while loading the homepage.")
        return redirect(url_for("main.index"))

@main.route("/processed_articles", methods=["GET"])
def processed_articles():
    try:
        page = request.args.get("page", 1, type=int)
        per_page = 10
        sort_by = request.args.get("sort_by", "processed_date")
        order = request.args.get("order", "desc")

        all_articles = get_all_articles()
        reverse = order == "desc"
        sorted_articles = sorted(
            all_articles,
            key=lambda x: x.get(sort_by, ""),
            reverse=reverse,
        )

        total_articles = len(sorted_articles)
        total_pages = (total_articles + per_page - 1) // per_page
        start = (page - 1) * per_page
        paginated_articles = sorted_articles[start:start + per_page]

        return render_template(
            "processed_articles.html",
            articles=paginated_articles,
            page=page,
            total_pages=total_pages,
            sort_by=sort_by,
            order=order,
        )
    except Exception as e:
        logging.error(f"Error loading processed articles: {e}")
        flash("An error occurred while loading the articles.")
        return redirect(url_for("main.index"))

@main.route("/article/<string:article_id>")
def article_detail(article_id):
    try:
        article = get_article_by_id(article_id)
        if not article:
            flash("Article not found.")
            return redirect(url_for("main.processed_articles"))
        return render_template("article_detail.html", article=article)
    except Exception as e:
        logging.error(f"Error loading article {article_id}: {e}")
        flash("An error occurred while loading the article details.")
        return redirect(url_for("main.processed_articles"))

@main.route("/delete_article/<string:article_id>", methods=["POST"])
def delete_article(article_id):
    try:
        delete_article_by_id(article_id)
        flash("Article deleted successfully.")
        return redirect(url_for("main.processed_articles"))
    except Exception as e:
        logging.error(f"Error deleting article {article_id}: {e}")
        flash("An error occurred while deleting the article.")
        return redirect(url_for("main.processed_articles"))

@main.route("/search_by_hashtag", methods=["GET"])
def search_by_hashtag():
    hashtag = request.args.get("hashtag", "").strip()
    if not hashtag:
        flash("No hashtag provided.")
        return redirect(url_for("main.processed_articles"))
    try:
        articles = get_articles_by_hashtag(hashtag)
        return render_template(
            "processed_articles.html",
            articles=articles,
            page=1,
            total_pages=1,
            sort_by=None,
            order=None,
        )
    except Exception as e:
        logging.error(f"Error searching by hashtag #{hashtag}: {e}")
        flash("An error occurred while searching.")
        return redirect(url_for("main.processed_articles"))

@main.route("/update_article/<string:article_id>", methods=["POST"])
def update_article_tags(article_id):
    new_hashtags = request.form.get("hashtags", "").split(",")
    try:
        update_article(
            article_id,
            {"hashtags": [tag.strip() for tag in new_hashtags if tag.strip()]},
        )
        flash("Article hashtags updated successfully.")
        return redirect(url_for("main.article_detail", article_id=article_id))
    except Exception as e:
        logging.error(f"Error updating hashtags for {article_id}: {e}")
        flash("An error occurred while updating hashtags.")
        return redirect(url_for("main.article_detail", article_id=article_id))

@main.route("/process_article", methods=["POST"])
def process_article():
    try:
        url = request.form.get("url", "").strip()
        hashtags = request.form.get("hashtags", "").strip().split(",")
        voice_name = request.form.get("voice_name", "").strip()

        article_data = extract_text_from_url(url)
        if not article_data.get("text"):
            return jsonify({"message": "Failed to extract text from article."}), 400

        output_file = generate_audio_file_path(article_data, "downloads")
        audio_length = text_to_speech(
            article_data["text"],
            output_file,
            metadata=article_data,
            voice_name=voice_name if voice_name else None,
        )
        download_link = upload_to_gcs(output_file, output_file.split("/")[-1])

        save_article_metadata(
            title=article_data["title"],
            source=article_data["source"],
            url=url,
            publish_date=article_data["publish_date"],
            download_link=download_link,
            authors=article_data["authors"],
            text_content=article_data["text"],
            hashtags=[tag.strip() for tag in hashtags if tag.strip()],
            voice_name=voice_name,
            audio_length=round(audio_length, 2),
        )

        return jsonify({
            "message": "Success",
            "audio_url": download_link,
            "details_url": url_for("main.processed_articles")
        }), 200

    except Exception as e:
        logging.error(f"Error processing article: {e}", exc_info=True)
        return jsonify({"message": "Unexpected error during article processing."}), 500
