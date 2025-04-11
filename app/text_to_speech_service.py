import logging
import tempfile
import os
import re
import time
from google.cloud import texttospeech
from pydub import AudioSegment
from typing import List, Dict, Optional

class TTSConversionError(Exception):
    """Custom exception for Text-to-Speech conversion errors."""
    pass

def split_text_by_bytes(text: str, max_bytes: int = 5000) -> List[str]:
    """Splits text into chunks that fit within a byte limit for TTS processing."""
    chunks, current_chunk = [], ""
    for sentence in re.split(r'(?<=[.!?]) +', text):
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
    retries: int = 3
) -> str:
    """Helper function to synthesize a text chunk with retries and save it to a temporary file."""
    for attempt in range(retries):
        try:
            synthesis_input = texttospeech.SynthesisInput(text=chunk)
            response = client.synthesize_speech(input=synthesis_input, voice=voice, audio_config=audio_config)

            # Write the audio content to a temporary file
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
    retries: int = 3
) -> None:
    """Converts text to speech in chunks, adds metadata as an intro, and saves as a single MP3 file."""
    client = texttospeech.TextToSpeechClient()
    voice = texttospeech.VoiceSelectionParams(
        language_code=language_code,
        ssml_gender=gender,
        name=voice_name if voice_name else None
    )
    audio_config = texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.MP3)

    # Use the metadata formatter to create an intro
    intro_text = format_metadata_text(metadata)

    # Combine intro with main text and split into manageable chunks
    full_text = intro_text + " " + text
    text_chunks = split_text_by_bytes(full_text)
    temp_files = []

    try:
        for i, chunk in enumerate(text_chunks):
            temp_file_path = synthesize_text_chunk(chunk, client, voice, audio_config, retries)
            temp_files.append(temp_file_path)
            logging.info(f"Generated audio for chunk {i + 1}/{len(text_chunks)}")

        # Concatenate all audio chunks into the final file
        combined_audio = AudioSegment.empty()
        for temp_file_path in temp_files:
            combined_audio += AudioSegment.from_mp3(temp_file_path)

        # Normalize audio to ensure consistent volume levels
        combined_audio = combined_audio.normalize()
        combined_audio.export(output_file, format="mp3")
        logging.info(f"Concatenated audio saved as: {output_file}")

    except TTSConversionError as e:
        logging.error(f"Error during text-to-speech conversion: {e}")
        raise
    finally:
        # Clean up temporary files
        for temp_file in temp_files:
            if os.path.exists(temp_file):
                os.remove(temp_file)
                logging.info(f"Deleted temporary file: {temp_file}")
