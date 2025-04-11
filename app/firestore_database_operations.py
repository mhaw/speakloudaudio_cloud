import datetime
import logging
import time
from google.cloud import firestore
from google.api_core.exceptions import GoogleAPICallError, RetryError

# Firestore client
firestore_client = firestore.Client()

def retry_on_failure(max_retries=3, delay=2):
    """Decorator for retrying Firestore operations in case of failure."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            retries = 0
            while retries < max_retries:
                try:
                    return func(*args, **kwargs)
                except (GoogleAPICallError, RetryError) as e:
                    logging.warning(f"Retry {retries + 1}/{max_retries} for {func.__name__} due to error: {e}")
                    retries += 1
                    time.sleep(delay)
            logging.error(f"Operation {func.__name__} failed after {max_retries} retries.")
            raise
        return wrapper
    return decorator

@retry_on_failure()
def save_article_metadata(title, source, url, publish_date, download_link, authors="Unknown",
                          text_content="", hashtags=[], voice_name=None, audio_length=None):
    """Saves metadata for a processed article into Firestore."""
    try:
        article_data = {
            "title": title,
            "source": source,
            "url": url,
            "publish_date": publish_date,
            "processed_date": datetime.datetime.now().strftime("%Y-%m-%d"),
            "download_link": download_link,
            "authors": authors,
            "text_content": text_content,
            "hashtags": hashtags,
        }

        if voice_name:
            article_data["voice_name"] = voice_name
        if audio_length is not None:
            article_data["audio_length"] = audio_length

        doc_ref = firestore_client.collection("articles").add(article_data)
        logging.info(f"Article metadata saved for URL: {url} with hashtags: {hashtags}")
        return doc_ref[1].id
    except Exception as e:
        logging.error(f"Firestore error while saving article metadata: {e}")
        raise
    
@retry_on_failure()
def get_all_articles():
    """Fetches all articles from Firestore and returns them as dictionaries."""
    try:
        articles_ref = firestore_client.collection("articles")
        articles = articles_ref.stream()
        all_articles = [{**article.to_dict(), "id": article.id} for article in articles]
        logging.info(f"Fetched {len(all_articles)} articles from Firestore.")
        return all_articles
    except Exception as e:
        logging.error(f"Firestore error while retrieving all articles: {e}")
        return []

@retry_on_failure()
def get_recent_articles(limit: int = 5) -> list:
    """Fetches a limited number of recently processed articles."""
    try:
        articles_ref = firestore_client.collection("articles").order_by("processed_date", direction=firestore.Query.DESCENDING).limit(limit)
        articles = articles_ref.stream()
        return [{**article.to_dict(), "id": article.id} for article in articles]
    except Exception as e:
        logging.error(f"Firestore error during recent articles fetch: {e}")
        return []

@retry_on_failure()
def update_article(article_id: str, update_data: dict):
    """Updates specific fields of an article in Firestore."""
    try:
        article_ref = firestore_client.collection("articles").document(article_id)
        article_ref.update(update_data)
        logging.info(f"Article with ID {article_id} updated successfully with data: {update_data}")
    except Exception as e:
        logging.error(f"Firestore error while updating article metadata: {e}")
        raise

@retry_on_failure()
def get_listen_count(article_id: str) -> int:
    """Returns the listen count for a given article ID."""
    try:
        article_ref = firestore_client.collection("articles").document(article_id)
        listens_ref = article_ref.collection("listens")
        listen_count = sum(1 for _ in listens_ref.stream())
        logging.info(f"Listen count for article ID {article_id}: {listen_count}")
        return listen_count
    except Exception as e:
        logging.error(f"Firestore error while counting listens: {e}")
        return 0

@retry_on_failure()
def get_article_by_id(article_id: str):
    """Fetches an article from Firestore by its ID."""
    try:
        article_ref = firestore_client.collection("articles").document(article_id)
        article = article_ref.get()
        if article.exists:
            logging.info(f"Article with ID {article_id} fetched successfully.")
            return {**article.to_dict(), "id": article.id}
        else:
            logging.warning(f"Article with ID {article_id} not found.")
            return None
    except Exception as e:
        logging.error(f"Firestore error while fetching article by ID: {e}")
        raise

@retry_on_failure()
def get_article_by_url(url: str):
    """Fetches an article from Firestore based on its URL."""
    try:
        articles_ref = firestore_client.collection("articles")
        query = articles_ref.where("url", "==", url).limit(1).stream()
        article = next(query, None)
        if article:
            logging.info(f"Article with URL {url} fetched successfully.")
            return {**article.to_dict(), "id": article.id}
        else:
            logging.warning(f"Article with URL {url} not found.")
            return None
    except Exception as e:
        logging.error(f"Firestore error while retrieving article by URL: {e}")
        return None

@retry_on_failure()
def delete_article_by_id(article_id: str):
    """Deletes an article from Firestore by its ID."""
    try:
        firestore_client.collection("articles").document(article_id).delete()
        logging.info(f"Article with ID {article_id} deleted successfully.")
    except Exception as e:
        logging.error(f"Firestore error while deleting article: {e}")
        raise

@retry_on_failure()
def get_articles_by_hashtag(hashtag: str) -> list:
    """Fetches all articles containing a specific hashtag."""
    try:
        articles_ref = firestore_client.collection("articles").where("hashtags", "array_contains", hashtag)
        articles = articles_ref.stream()
        articles_with_hashtag = [{**article.to_dict(), "id": article.id} for article in articles]
        logging.info(f"Fetched {len(articles_with_hashtag)} articles with hashtag #{hashtag}.")
        return articles_with_hashtag
    except Exception as e:
        logging.error(f"Firestore error while retrieving articles by hashtag: {e}")
        return []
