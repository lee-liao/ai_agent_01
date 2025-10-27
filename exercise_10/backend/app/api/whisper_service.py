import openai
from fastapi import UploadFile
import io
from ..config import settings

async def transcribe_audio(audio_data: bytes, filename: str = "audio.wav"):
    """
    Transcribes an audio file using OpenAI's Whisper model.
    Handles raw PCM audio data by wrapping it in WAV format for Whisper compatibility.
    """
    try:
        # Create a new client instance with the current API key
        client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        
        # Check if audio_data is raw PCM that needs to be wrapped in WAV format
        # The audio_data here is already in WAV format from the conversion in websocket.py
        audio_file = io.BytesIO(audio_data)
        audio_file.name = filename
        
        transcript = await client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file
        )
        return transcript.text
    except Exception as e:
        print(f"Error transcribing audio: {e}")
        return None