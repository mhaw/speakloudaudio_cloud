import logging
import tempfile
import os
import time
from google.cloud import texttospeech
from pydub import AudioSegment
from typing import List, Dict, Optional
import nltk
from nltk.tokenize import sent_tokenize

class TTSConversionError(Exception):
    """Custom exception for Text-to-Speech conversion errors."""
    pass

nltk.download('punkt')

def split_text_by_bytes(text: str, max_bytes: int = 5000) -> List[str]:
    """Splits text into chunks using nltk sentence tokenizer and byte limit."""
    chunks, current_chunk = [], ""
    for sentence in sent_tokenize(text):
        sentence_bytes = len(sentence.encode('utf-8'))
        if len(current_chunk.encode('utf-8')) + sentence_bytes <= max_bytes:
            current_chunk += sentence + " "
        else:
            chunks.append(current_chunk.strip())
            current_chunk = sentence + " "
    if current_chunk:
        chunks.append(current_chunk.strip())
    logging.info(f"Split text into {len(chunks)} chunks.")
    return chunks

def format_metadata_text(metadata: Dict[str, str]) -> str:
    """Formats metadata text into a readable intro for the audio."""
    return (
        f"Title: {metadata.get('title', 'Unknown Title')}. "
        f"Source: {metadata.get('source', 'Unknown Source')}. "
        f"Author(s): {metadata.get('authors', 'Unknown Author')}. "
        f"Published on: {metadata.get('publish_date', 'Unknown Date')}."
    )

def synthesize_text_chunk(
    chunk: str,
    client: texttospeech.TextToSpeechClient,
    voice: texttospeech.VoiceSelectionParams,
    audio_config: texttospeech.AudioConfig,
    use_ssml: bool = False,
    retries: int = 3
) -> str:
    """Synthesizes a text chunk with retries, optionally using SSML."""
    for attempt in range(retries):
        try:
            input_data = texttospeech.SynthesisInput(ssml=f"<speak>{chunk}</speak>") if use_ssml else texttospeech.SynthesisInput(text=chunk)
            response = client.synthesize_speech(input=input_data, voice=voice, audio_config=audio_config)

            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
            temp_file.write(response.audio_content)
            temp_file.close()
            return temp_file.name

        except Exception as e:
            if attempt < retries - 1:
                backoff_time = 2 ** attempt
                logging.warning(f"Retry {attempt + 1}/{retries} for chunk due to error: {e}. Backing off for {backoff_time} seconds.")
                time.sleep(backoff_time)
            else:
                logging.error(f"Final attempt failed for chunk: {e}")
                raise TTSConversionError(f"Failed to synthesize chunk after {retries} attempts.")

def text_to_speech(
    text: str,
    output_file: str,
    metadata: Dict[str, str],
    language_code: str = "en-US",
    gender: texttospeech.SsmlVoiceGender = texttospeech.SsmlVoiceGender.NEUTRAL,
    voice_name: Optional[str] = None,
    use_ssml: bool = False,
    retries: int = 3
) -> float:
    """Converts text to speech, normalizes volume, and returns audio length in seconds."""
    client = texttospeech.TextToSpeechClient()
    voice = texttospeech.VoiceSelectionParams(
        language_code=language_code,
        ssml_gender=gender,
        name=voice_name if voice_name else None
    )
    audio_config = texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.MP3)

    intro_text = format_metadata_text(metadata)
    full_text = f"{intro_text} {text}"
    text_chunks = split_text_by_bytes(full_text)
    temp_files = []

    try:
        for i, chunk in enumerate(text_chunks):
            temp_file_path = synthesize_text_chunk(chunk, client, voice, audio_config, use_ssml, retries)
            temp_files.append(temp_file_path)
            logging.info(f"Generated audio for chunk {i + 1}/{len(text_chunks)}")

        combined_audio = AudioSegment.empty()
        for temp_file_path in temp_files:
            combined_audio += AudioSegment.from_mp3(temp_file_path)

        combined_audio = combined_audio.normalize()
        combined_audio.export(output_file, format="mp3")
        logging.info(f"Concatenated audio saved as: {output_file}")

        return combined_audio.duration_seconds

    except TTSConversionError as e:
        logging.error(f"Error during text-to-speech conversion: {e}")
        raise
    finally:
        for temp_file in temp_files:
            if os.path.exists(temp_file):
                os.remove(temp_file)
                logging.info(f"Deleted temporary file: {temp_file}")
