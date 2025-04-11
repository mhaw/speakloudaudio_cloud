# run.py
from flask import Flask
from google.cloud import firestore
import os
from config import Config
import logging

# Import Blueprint from routes
try:
    from app.routes import main
except ImportError as e:
    logging.error(f"Failed to import routes: {e}")
    raise

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Validate environment variables
REQUIRED_ENV_VARS = ["GCS_BUCKET_NAME", "GOOGLE_APPLICATION_CREDENTIALS"]
missing_vars = [var for var in REQUIRED_ENV_VARS if not os.getenv(var)]
if missing_vars:
    logging.error(f"Missing required environment variables: {', '.join(missing_vars)}")
    raise EnvironmentError(f"Missing required environment variables: {', '.join(missing_vars)}")

# Create Flask app and specify the template and static folder locations
app = Flask(__name__, template_folder="app/templates", static_folder="app/static")
app.config.from_object(Config)

# Register the Blueprint
app.register_blueprint(main)

# Check and log GCS_BUCKET_NAME
GCS_BUCKET_NAME = os.getenv("GCS_BUCKET_NAME")
logging.info(f"Using GCS_BUCKET_NAME: {GCS_BUCKET_NAME}")

# Initialize Firestore database
firestore_db = None

def initialize_firestore():
    global firestore_db
    google_credentials = Config.GOOGLE_APPLICATION_CREDENTIALS
    if google_credentials and os.path.isfile(google_credentials):
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = google_credentials
        logging.info("GOOGLE_APPLICATION_CREDENTIALS set successfully.")
    else:
        logging.error("GOOGLE_APPLICATION_CREDENTIALS file is missing or invalid.")
        raise EnvironmentError("Valid GOOGLE_APPLICATION_CREDENTIALS is required.")
    try:
        firestore_db = firestore.Client()
        logging.info("Firestore successfully initialized.")
    except Exception as e:
        logging.error(f"Failed to initialize Firestore: {e}")
        raise

initialize_firestore()

# Make Firestore client accessible across the app
@app.before_request
def setup_firestore():
    if firestore_db:
        app.config["firestore_db"] = firestore_db

# Health check endpoint
@app.route("/health")
def health():
    try:
        if firestore_db:
            firestore_db.collection("test").limit(1).get()  # Quick test query
        return "Healthy", 200
    except Exception as e:
        logging.error(f"Health check failed: {e}")
        return "Unhealthy", 500

# Run the app with proper environment port binding
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))  # Default to Cloud Run port 8080
    debug_mode = os.environ.get("FLASK_DEBUG", "False").lower() == "true"
    logging.info(f"Starting app on port {port} with debug={debug_mode}")
    app.run(host="0.0.0.0", port=port, debug=debug_mode)
