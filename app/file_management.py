import os
import re
import logging
from datetime import datetime
from urllib.parse import urlparse
from typing import Optional, Dict, Union

# Limit for filename length to ensure compatibility with most filesystems.
FILENAME_LENGTH_LIMIT = 255

# Mapping for more human-readable source names based on domain.
SOURCE_NAME_MAPPING = {
    "theatlantic.com": "The_Atlantic",
    "newyorker.com": "The_New_Yorker",
    "washingtonpost.com": "Washington_Post",
    "defector.com": "Defector",
    "nytimes.com": "New_York_Times",
    "bbc.com": "BBC",
}

def get_human_readable_source(url: str) -> str:
    """Extracts a human-readable source name from the URL."""
    domain = urlparse(url).netloc.replace("www.", "").lower()
    return SOURCE_NAME_MAPPING.get(domain, re.sub(r'[^a-zA-Z0-9]+', '_', domain).title())

def sanitize_title(title: str, limit: int = 50) -> str:
    """Sanitizes the title to be a valid filename by replacing invalid characters and limiting length."""
    sanitized = re.sub(r'[^a-zA-Z0-9]+', '_', title).strip('_')
    return sanitized[:limit]  # Limit the length to ensure filenames are not too long.

def sanitize_filename(filename: str) -> str:
    """Truncates and sanitizes a filename to fit within file system constraints."""
    return filename[:FILENAME_LENGTH_LIMIT]

def generate_audio_file_name(article_metadata: Dict[str, str], directory: str = "downloads") -> str:
    """Generates a unique filename for the audio file based on the article metadata."""
    # Get or generate publish date
    publish_date = article_metadata.get("publish_date", datetime.now().strftime("%Y_%m_%d"))

    # Extract source and title, sanitize them for filename safety, and truncate them to reasonable lengths.
    source_url = article_metadata.get("source", "")
    source = get_human_readable_source(source_url)
    title = sanitize_title(article_metadata.get("title", "title_unknown"), limit=50)

    # Create a base name for the file
    base_name = f"{publish_date}_{source[:20]}_{title}".lower()
    filename = sanitize_filename(f"{base_name}.mp3")

    # Ensure the filename is unique by appending a counter if needed.
    counter = 1
    while os.path.exists(os.path.join(directory, filename)):
        filename = sanitize_filename(f"{base_name}_{counter}.mp3")
        counter += 1

    return filename

def generate_audio_file_path(article_metadata: Dict[str, str], directory: str = "downloads") -> str:
    """Generates the complete file path for the audio file."""
    create_directory_if_not_exists(directory)  # Ensure the directory exists
    filename = generate_audio_file_name(article_metadata, directory)
    return os.path.join(directory, filename)

def create_directory_if_not_exists(directory: str) -> None:
    """Creates the directory if it does not exist."""
    try:
        os.makedirs(directory, exist_ok=True)
        logging.info(f"Directory '{directory}' is ready.")
    except Exception as e:
        logging.error(f"Failed to create directory '{directory}': {e}")
        raise OSError(f"Failed to create directory {directory}: {e}")

def extract_metadata(article_metadata: Dict[str, Union[str, list]]) -> Dict[str, str]:
    """Extracts and formats additional metadata from the article."""
    # Extract the first author, or set to 'Unknown Author' if none is provided
    authors_list = article_metadata.get("authors", [])
    first_author = authors_list[0] if authors_list else "Unknown Author"

    # Handle date formatting if the publish date is a datetime object
    publish_date = article_metadata.get("publish_date", "Unknown Date")
    if isinstance(publish_date, datetime):
        publish_date = publish_date.strftime("%Y-%m-%d")

    return {
        "title": article_metadata.get("title", "Unknown Title"),
        "source": get_human_readable_source(article_metadata.get("source", "")),
        "publish_date": publish_date,
        "authors": first_author
    }

def is_valid_path(directory: str) -> bool:
    """Checks if a directory path is valid."""
    try:
        if not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
        return True
    except Exception as e:
        logging.error(f"Invalid directory path '{directory}': {e}")
        return False

def clean_metadata_string(value: Optional[str], default: str = "Unknown") -> str:
    """Cleans a metadata value by ensuring it is a string and not empty."""
    if not value or not isinstance(value, str):
        return default
    return value.strip()[:FILENAME_LENGTH_LIMIT]  # Ensure value length is within limits

def validate_article_metadata(article_metadata: Dict[str, Union[str, list]]) -> bool:
    """Validates the article metadata for essential fields."""
    required_fields = ["title", "source"]
    for field in required_fields:
        if field not in article_metadata or not article_metadata[field]:
            logging.warning(f"Article metadata missing required field: {field}")
            return False
    return True
