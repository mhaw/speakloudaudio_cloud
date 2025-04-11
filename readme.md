# SpeakLoudAudio

Convert articles from the web into spoken audio using Google Cloud Text-to-Speech and Firestore for metadata storage.

## Features

- 🗞 Extracts clean article content and metadata from any URL
- 🔊 Converts text to high-quality audio (MP3) using Google Cloud TTS
- 🎤 Choose from multiple voice options (e.g., Wavenet voices)
- ⏱ Displays audio duration for each article
- 📊 Tracks listen counts per article
- 🏷 Tag articles with hashtags for filtering and search
- 📁 Stores metadata in Firestore and audio files in Google Cloud Storage
- 🌙 Dark mode UI with TailwindCSS
- 🎧 Web-based audio playback, sharing, and metadata editing

## Requirements

- Python 3.10+
- Google Cloud project with:
  - Text-to-Speech API enabled
  - Firestore (in Native mode)
  - Storage bucket
- `GOOGLE_APPLICATION_CREDENTIALS` environment variable set to your service account JSON file

## Setup

```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Download sentence tokenizer for text chunking
python -m nltk.downloader punkt
```

## Running Locally

```bash
export FLASK_APP=app
export FLASK_ENV=development
flask run
```

## Docker Workflow

### 1. Build
```bash
docker build -t gcr.io/speakloudaudio/speakloudaudio_cloud:latest .
```

### 2. Push
```bash
docker push gcr.io/speakloudaudio/speakloudaudio_cloud:latest
```

### 3. Deploy
```bash
gcloud run deploy speakloudaudio-service \
  --image gcr.io/speakloudaudio/speakloudaudio_cloud:latest \
  --platform managed \
  --region us-east1 \
  --allow-unauthenticated \
  --service-account=speakloudaudio-cloud-admin@speakloudaudio.iam.gserviceaccount.com \
  --memory=512Mi \
  --timeout=300s
```

## File Structure

```
app/
├── templates/                 # HTML templates (TailwindCSS-based)
├── static/                    # CSS styles and JS
├── routes.py                  # Flask routing logic
├── services.py                # Article processing orchestration
├── text_to_speech_service.py # Google TTS logic
├── text_extraction.py        # Content extraction from URLs
├── firestore_database_operations.py
├── cloud_storage.py          # Upload audio to GCS
├── file_management.py        # Paths and metadata formatting
```

## Credits & License

Built by [you!] for educational and experimental purposes. MIT License. Contributions welcome!
