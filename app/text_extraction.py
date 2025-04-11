import datetime
import logging
import time
from newspaper import Article, Config
from bs4 import BeautifulSoup
from typing import Dict, Any
import requests
from requests.exceptions import HTTPError, RequestException

# Optional: fallback parser
try:
    import trafilatura
    TRAFILATURA_AVAILABLE = True
except ImportError:
    TRAFILATURA_AVAILABLE = False

# Custom User-Agent header to avoid bot detection
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Referer": "https://www.google.com/",
    "Accept-Language": "en-US,en;q=0.9",
}

def remove_repeated_paragraphs(text: str) -> str:
    seen = set()
    cleaned = []
    for paragraph in text.split('\n'):
        trimmed = paragraph.strip()
        if trimmed and trimmed not in seen:
            cleaned.append(trimmed)
            seen.add(trimmed)
    return '\n\n'.join(cleaned)

def extract_text_from_url(url: str, retries: int = 3, backoff_factor: int = 2) -> Dict[str, Any]:
    """
    Extracts article text, title, and author information from the provided URL.
    Returns a dictionary containing the text and metadata.
    Retries extraction with exponential backoff if it fails.
    """
    article_data = {
        "title": "Unknown Title",
        "text": "",
        "authors": ["Unknown Author"],
        "publish_date": "Unknown Date",
        "source": url
    }

    # Try enhanced handling for known problematic domains
    domain = requests.utils.urlparse(url).netloc
    use_trafilatura = ("nytimes.com" in domain) and TRAFILATURA_AVAILABLE

    if use_trafilatura:
        logging.info("Using trafilatura for URL: %s", url)
        try:
            downloaded = trafilatura.fetch_url(url)
            if downloaded:
                result = trafilatura.extract(downloaded, include_comments=False, include_tables=False)
                if result:
                    article_data["text"] = remove_repeated_paragraphs(result)
                    article_data["title"] = url  # Trafilatura lacks title extraction
                    return article_data
        except Exception as e:
            logging.warning(f"Trafilatura fallback failed for {url}: {e}")

    # Retry loop for newspaper3k
    for attempt in range(retries):
        try:
            user_agent_config = Config()
            user_agent_config.browser_user_agent = HEADERS['User-Agent']
            user_agent_config.request_timeout = 15

            article = Article(url, config=user_agent_config)
            article.download()
            article.parse()

            article_data["title"] = article.title or article_data["title"]
            article_data["text"] = remove_repeated_paragraphs(article.text or "")
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

    # Fallback using BeautifulSoup
    try:
        logging.info(f"Attempting fallback extraction using BeautifulSoup for URL: {url}")
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')
        title_tag = soup.find('title')
        if title_tag:
            article_data["title"] = title_tag.text.strip()

        paragraphs = soup.find_all('p')
        if paragraphs:
            raw_text = "\n".join(p.get_text().strip() for p in paragraphs)
            article_data["text"] = remove_repeated_paragraphs(raw_text)

        logging.info(f"Fallback extraction successful for URL: {url}")

    except HTTPError as http_err:
        logging.error(f"HTTP error during fallback extraction for {url}: {http_err}")
    except RequestException as req_err:
        logging.error(f"Request error during fallback extraction for {url}: {req_err}")
    except Exception as e:
        logging.error(f"Unexpected error during fallback extraction for {url}: {e}")

    return article_data
