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
    Extracts article text, title, and author information from the provided URL.
    Returns a dictionary containing the text and metadata.
    Retries extraction with exponential backoff if it fails.
    """
    # Initialize article data with default values
    article_data = {
        "title": "Unknown Title",
        "text": "",
        "authors": ["Unknown Author"],
        "publish_date": "Unknown Date",
        "source": url
    }

    # Retry mechanism for transient errors
    for attempt in range(retries):
        try:
            # Configuration to set up headers
            user_agent_config = Config()
            user_agent_config.browser_user_agent = HEADERS['User-Agent']
            user_agent_config.request_timeout = 15  # Timeout for newspaper

            # Attempt to extract using newspaper3k
            article = Article(url, config=user_agent_config)
            article.download()
            article.parse()

            # Extract and set article data, falling back to defaults if any are empty
            article_data["title"] = article.title if article.title else "Unknown Title"
            article_data["text"] = article.text if article.text else ""
            article_data["authors"] = article.authors if article.authors else ["Unknown Author"]
            if article.publish_date:
                article_data["publish_date"] = article.publish_date.strftime("%Y-%m-%d")

            logging.info(f"Successfully extracted article data from URL: {url}")
            return article_data

        except HTTPError as http_err:
            logging.warning(f"HTTP error occurred on attempt {attempt + 1}/{retries} for URL {url}: {http_err}")
        except RequestException as req_err:
            logging.warning(f"Request error occurred on attempt {attempt + 1}/{retries} for URL {url}: {req_err}")
        except Exception as e:
            logging.error(f"An error occurred on attempt {attempt + 1}/{retries} for URL {url}: {e}")

        # Exponential backoff
        time.sleep(backoff_factor ** attempt)

    # Fallback mechanism using requests and BeautifulSoup
    try:
        logging.info(f"Attempting fallback extraction using requests and BeautifulSoup for URL: {url}")
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')

        # Extract title
        title_tag = soup.find('title')
        if title_tag:
            article_data["title"] = title_tag.text.strip()

        # Extract text from <p> tags
        paragraphs = soup.find_all('p')
        if paragraphs:
            article_data["text"] = " ".join(p.get_text().strip() for p in paragraphs)

        logging.info(f"Fallback extraction successful for URL: {url}")

    except HTTPError as http_err:
        logging.error(f"HTTP error occurred during fallback extraction for URL {url}: {http_err}")
    except RequestException as req_err:
        logging.error(f"Request error occurred during fallback extraction for URL {url}: {req_err}")
    except Exception as e:
        logging.error(f"Unexpected error during fallback extraction for URL {url}: {e}")

    return article_data
