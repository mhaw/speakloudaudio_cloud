import os
import logging
import traceback
import time
from google.cloud import storage
from typing import Optional

class UploadError(Exception):
    pass

def upload_to_gcs(local_path: str, filename: str, retries: int = 3) -> Optional[str]:
    """Uploads a file to Google Cloud Storage, with retry logic."""
    bucket_name = os.getenv("GCS_BUCKET_NAME")
    if not bucket_name:
        logging.error("GCS_BUCKET_NAME environment variable is not set.")
        raise EnvironmentError("GCS_BUCKET_NAME is required.")
    
    try:
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(filename)
        
        logging.info(f"Uploading {filename} to Google Cloud Storage...")
        for attempt in range(retries):
            try:
                blob.upload_from_filename(local_path)
                logging.info(f"File {filename} successfully uploaded.")
                return blob.public_url
            except (storage.exceptions.GoogleAPIError, storage.exceptions.RetryError) as e:
                if attempt < retries - 1:
                    backoff_time = 2 ** attempt  # Exponential backoff
                    logging.warning(f"Retrying upload in {backoff_time} seconds... Attempt {attempt + 1}")
                    time.sleep(backoff_time)
                else:
                    logging.error(f"Upload failed after {retries} attempts.")
                    logging.error(traceback.format_exc())
                    raise UploadError(f"Failed to upload {filename} to Google Cloud Storage.")
    except Exception as e:
        logging.error(f"Unexpected error uploading file to GCS: {e}")
        logging.error(traceback.format_exc())
        raise
