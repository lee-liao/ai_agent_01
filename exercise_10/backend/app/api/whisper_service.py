import io
from typing import Optional

from fastapi import HTTPException
from openai import AsyncOpenAI


class WhisperService:
    def __init__(self, api_key: str):
        # Lazy client init to avoid startup errors with missing/invalid deps
        self._api_key = api_key
        self.client: Optional[AsyncOpenAI] = None

    async def transcribe_audio(self, audio_bytes: bytes) -> str:
        """Transcribe audio bytes using OpenAI Whisper API.

        Expects WebM/Opus chunks; wraps bytes in a file-like object.
        Returns text or empty string on no content.
        """
        if not self._api_key:
            raise HTTPException(status_code=500, detail="OPENAI_API_KEY not configured")
        if self.client is None:
            self.client = AsyncOpenAI(api_key=self._api_key)

        try:
            audio_file = io.BytesIO(audio_bytes)
            # Name attribute hints content type to SDK
            audio_file.name = "audio.webm"

            resp = await self.client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
            )
            # resp has .text in SDK v1.x
            return getattr(resp, "text", "") or ""
        except Exception as e:
            # Bubble up as HTTPException for consistent error handling
            raise HTTPException(status_code=500, detail=f"Whisper error: {e}")
