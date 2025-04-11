import os
import logging
import google.auth
import google.cloud.firestore as firestore
import google.cloud.storage as storage
import google.cloud.texttospeech as texttospeech
from google.api_core.exceptions import GoogleAPICallError, PermissionDenied
from google.cloud.exceptions import NotFound

def test_firestore():
    try:
        credentials, project = google.auth.default()
        firestore_client = firestore.Client(credentials=credentials, project=project)
        # Create a test document
        doc_ref = firestore_client.collection('test_collection').document('test_document')
        doc_ref.set({'test_field': 'test_value'})
        # Read back the document
        doc = doc_ref.get()
        if doc.exists:
            print("Firestore: Successfully wrote and read test document.")
        else:
            print("Firestore: Test document could not be read.")
        # Clean up the test document
        doc_ref.delete()
    except PermissionDenied as e:
        print("Firestore: Permission denied. Please check your IAM roles.")
        logging.error(e)
    except GoogleAPICallError as e:
        print("Firestore: API call failed. Please check your configuration.")
        logging.error(e)
    except Exception as e:
        print("Firestore: An unexpected error occurred.")
        logging.error(e)

def test_cloud_storage():
    try:
        bucket_name = os.getenv("GCS_BUCKET_NAME")
        if not bucket_name:
            raise ValueError("Environment variable GCS_BUCKET_NAME is not set.")
        credentials, project = google.auth.default()
        storage_client = storage.Client(credentials=credentials, project=project)
        bucket = storage_client.bucket(bucket_name)
        # Create a test blob (file)
        blob = bucket.blob("test_blob.txt")
        blob.upload_from_string("This is a test.")
        # Read back the blob
        downloaded_data = blob.download_as_text()
        if downloaded_data == "This is a test.":
            print("Cloud Storage: Successfully uploaded and read test blob.")
        else:
            print("Cloud Storage: Test blob could not be read properly.")
        # Clean up the test blob
        blob.delete()
    except NotFound as e:
        print("Cloud Storage: Bucket not found. Please check your bucket name.")
        logging.error(e)
    except PermissionDenied as e:
        print("Cloud Storage: Permission denied. Please check your IAM roles.")
        logging.error(e)
    except GoogleAPICallError as e:
        print("Cloud Storage: API call failed. Please check your configuration.")
        logging.error(e)
    except Exception as e:
        print("Cloud Storage: An unexpected error occurred.")
        logging.error(e)

def test_text_to_speech():
    try:
        credentials, project = google.auth.default()
        tts_client = texttospeech.TextToSpeechClient(credentials=credentials)
        synthesis_input = texttospeech.SynthesisInput(text="This is a test.")
        voice = texttospeech.VoiceSelectionParams(language_code="en-US", ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL)
        audio_config = texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.MP3)
        # Perform the Text-to-Speech request
        response = tts_client.synthesize_speech(input=synthesis_input, voice=voice, audio_config=audio_config)
        if response.audio_content:
            print("Text-to-Speech: Successfully generated test audio.")
        else:
            print("Text-to-Speech: No audio content returned.")
    except PermissionDenied as e:
        print("Text-to-Speech: Permission denied. Please check your IAM roles.")
        logging.error(e)
    except GoogleAPICallError as e:
        print("Text-to-Speech: API call failed. Please check your configuration.")
        logging.error(e)
    except Exception as e:
        print("Text-to-Speech: An unexpected error occurred.")
        logging.error(e)

if __name__ == "__main__":
    logging.basicConfig(level=logging.ERROR)
    print("Testing Firestore access...")
    test_firestore()
    print("\nTesting Cloud Storage access...")
    test_cloud_storage()
    print("\nTesting Text-to-Speech access...")
    test_text_to_speech()
