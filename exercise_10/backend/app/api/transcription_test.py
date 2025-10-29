from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
import io
import logging
from .whisper_service import transcribe_audio

# Create router
router = APIRouter(prefix="/api/transcription", tags=["Transcription Test"])

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@router.post("/transcribe")
async def transcribe_audio_endpoint(file: UploadFile = File(...)):
    """
    Transcribe uploaded audio file using Whisper API
    """
    try:
        logger.info(f"Received audio file: {file.filename}, size: {file.size}, content-type: {file.content_type}")
        
        # Read the file content
        audio_data = await file.read()
        
        # Log the size of received data
        logger.info(f"Received {len(audio_data)} bytes of audio data")
        
        # Use the existing transcribe_audio function
        transcript = await transcribe_audio(audio_data, file.filename or "audio.webm")
        
        if transcript:
            logger.info(f"Transcription successful: {transcript[:50]}...")
            return JSONResponse(
                content={
                    "success": True,
                    "transcript": transcript,
                    "filename": file.filename,
                    "size": len(audio_data)
                }
            )
        else:
            logger.warning("Transcription returned empty result")
            return JSONResponse(
                content={
                    "success": False,
                    "error": "Transcription failed or returned empty result",
                    "filename": file.filename,
                    "size": len(audio_data)
                }
            )
            
    except Exception as e:
        logger.error(f"Error transcribing audio: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error transcribing audio: {str(e)}")

# Add the new router to the main app
def register_transcription_routes(app):
    """
    Function to register transcription test routes with the main app
    """
    app.include_router(router)