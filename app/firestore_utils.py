import datetime
import logging
from google.cloud import firestore

# Firestore client
firestore_client = firestore.Client()

def log_listen_event(article_id: str, count_only=False) -> int:
    """Logs a listen event or returns the listen count for a given article ID.
    
    Args:
        article_id (str): The ID of the article to log or count listens for.
        count_only (bool): If True, returns the listen count without logging.

    Returns:
        int: Listen count if `count_only` is True, else returns 1 on success, 0 on failure.
    """
    try:
        article_ref = firestore_client.collection("articles").document(article_id)
        listens_ref = article_ref.collection("listens")

        if count_only:
            listen_count = sum(1 for _ in listens_ref.stream())  # Efficiently count listens
            logging.info(f"Listen count retrieved for article ID {article_id}: {listen_count}")
            return listen_count
        else:
            listen_data = {
                "listen_date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            listens_ref.add(listen_data)
            logging.info(f"Listen event logged for article ID: {article_id}")
            return 1
    except Exception as e:
        logging.error(f"Firestore error in log_listen_event: {e}")
        return 0

def get_article_id_by_filename(filename: str) -> str:
    """Fetches the article ID based on the audio filename.
    
    Args:
        filename (str): The filename used to find the article.

    Returns:
        str: The article ID if found, else None.
    """
    try:
        articles_ref = firestore_client.collection("articles")
        query = articles_ref.where("download_link", "==", filename).limit(1).stream()
        article = next(query, None)
        if article:
            logging.info(f"Article ID fetched for filename: {filename}")
            return article.id
        else:
            logging.warning(f"Article not found for filename: {filename}")
            return None
    except Exception as e:
        logging.error(f"Firestore error in get_article_id_by_filename: {e}")
        return None

def format_date(date_string: str, format_string: str = "%Y-%m-%d") -> str:
    """Formats a date string into a specified format.
    
    Args:
        date_string (str): The date string to format.
        format_string (str): The format to convert to (default is "%Y-%m-%d").

    Returns:
        str: The formatted date string, or the original if an error occurs.
    """
    try:
        date_obj = datetime.datetime.strptime(date_string, "%Y-%m-%d")
        return date_obj.strftime(format_string)
    except ValueError as e:
        logging.error(f"Date formatting error: {e}")
        return date_string  # Return the original string if there's an error

def get_recent_activity(article_id: str, limit: int = 5) -> list:
    """Fetches recent listen events for a given article ID, limited to the specified number.
    
    Args:
        article_id (str): The ID of the article.
        limit (int): Number of recent events to fetch (default is 5).

    Returns:
        list: List of recent listen events, each as a dictionary.
    """
    try:
        article_ref = firestore_client.collection("articles").document(article_id)
        listens_ref = article_ref.collection("listens").order_by("listen_date", direction=firestore.Query.DESCENDING).limit(limit)
        listens = listens_ref.stream()
        recent_activity = [{"listen_date": listen.to_dict().get("listen_date")} for listen in listens]
        logging.info(f"Fetched {len(recent_activity)} recent listen events for article ID {article_id}")
        return recent_activity
    except Exception as e:
        logging.error(f"Firestore error in get_recent_activity: {e}")
        return []

def log_error(error_message: str):
    """Logs an error message for troubleshooting.
    
    Args:
        error_message (str): The error message to log.
    """
    logging.error(f"App error: {error_message}")
