import os

class Config:
    # Flask configuration
    SECRET_KEY = os.getenv("SECRET_KEY", "hawsmith1")
    
    # Google Cloud configuration
    GOOGLE_APPLICATION_CREDENTIALS = os.getenv(
        "GOOGLE_APPLICATION_CREDENTIALS", "/app/speakloudaudio-7a34eeceb530.json"
    )
    GCS_BUCKET_NAME = os.getenv("GCS_BUCKET_NAME", "speakloudaudio")

    # App-specific settings
    TTS_LANGUAGE_CODE = os.getenv("TTS_LANGUAGE_CODE", "en-US")
    TTS_VOICE_GENDER = os.getenv("TTS_VOICE_GENDER", "NEUTRAL")
    
    # Database configuration (Firestore in this case)
    FIRESTORE_PROJECT_ID = os.getenv("FIRESTORE_PROJECT_ID", "speakloudaudio")

    # Logging configuration
    LOG_LEVEL = os.getenv("LOG_LEVEL", "DEBUG")