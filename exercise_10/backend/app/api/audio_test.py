"""
Audio Test Endpoint
Test audio recording and transcription without ffmpeg
"""
from fastapi import APIRouter, UploadFile, File
from fastapi.responses import HTMLResponse
import io
import wave
from datetime import datetime
import os

from ..config import settings
from .whisper_service import transcribe_audio

router = APIRouter(tags=["Audio Test"])

@router.get("/test/audio", response_class=HTMLResponse)
async def audio_test_page():
    """Serve the audio test page"""
    html_content = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Audio Transcription Test</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            max-width: 800px;
            margin: 50px auto;
            padding: 20px;
            background: #f5f5f5;
        }
        .container {
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        h1 {
            color: #333;
            margin-bottom: 10px;
        }
        .subtitle {
            color: #666;
            margin-bottom: 30px;
        }
        button {
            padding: 12px 24px;
            margin: 10px 5px;
            font-size: 16px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            transition: all 0.3s;
        }
        .record-btn {
            background: #4CAF50;
            color: white;
        }
        .record-btn:hover {
            background: #45a049;
        }
        .record-btn:disabled {
            background: #ccc;
            cursor: not-allowed;
        }
        .stop-btn {
            background: #f44336;
            color: white;
        }
        .stop-btn:hover {
            background: #da190b;
        }
        .test-btn {
            background: #2196F3;
            color: white;
        }
        .test-btn:hover {
            background: #0b7dda;
        }
        .status {
            padding: 15px;
            margin: 20px 0;
            border-radius: 5px;
            display: none;
        }
        .status.info {
            background: #e3f2fd;
            border-left: 4px solid #2196F3;
            display: block;
        }
        .status.success {
            background: #e8f5e9;
            border-left: 4px solid #4CAF50;
            display: block;
        }
        .status.error {
            background: #ffebee;
            border-left: 4px solid #f44336;
            display: block;
        }
        .recording {
            animation: pulse 1.5s infinite;
        }
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        .result {
            margin-top: 20px;
            padding: 20px;
            background: #f9f9f9;
            border-radius: 5px;
            border-left: 4px solid #2196F3;
        }
        .result h3 {
            margin-top: 0;
            color: #333;
        }
        .transcript {
            font-size: 18px;
            color: #555;
            line-height: 1.6;
            padding: 15px;
            background: white;
            border-radius: 5px;
            margin-top: 10px;
        }
        .audio-info {
            margin-top: 10px;
            font-size: 14px;
            color: #666;
        }
        .controls {
            margin: 20px 0;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎤 Audio Transcription Test</h1>
        <p class="subtitle">Test speech-to-text without ffmpeg using Python's wave module</p>
        
        <div class="controls">
            <button id="recordBtn" class="record-btn">🎙️ Start Recording</button>
            <button id="stopBtn" class="stop-btn" disabled>⏹️ Stop Recording</button>
            <button id="testBtn" class="test-btn" disabled>🧪 Test Transcription</button>
        </div>
        
        <div id="status" class="status"></div>
        
        <div id="result" style="display: none;" class="result">
            <h3>Transcription Result:</h3>
            <div id="transcript" class="transcript"></div>
            <div id="audioInfo" class="audio-info"></div>
        </div>
    </div>

    <script>
        let mediaRecorder;
        let audioChunks = [];
        let recordedBlob;

        const recordBtn = document.getElementById('recordBtn');
        const stopBtn = document.getElementById('stopBtn');
        const testBtn = document.getElementById('testBtn');
        const statusDiv = document.getElementById('status');
        const resultDiv = document.getElementById('result');
        const transcriptDiv = document.getElementById('transcript');
        const audioInfoDiv = document.getElementById('audioInfo');

        function showStatus(message, type = 'info') {
            statusDiv.textContent = message;
            statusDiv.className = `status ${type}`;
        }

        recordBtn.addEventListener('click', async () => {
            try {
                const stream = await navigator.mediaDevices.getUserMedia({ 
                    audio: {
                        channelCount: 1,
                        sampleRate: 16000
                    } 
                });
                
                mediaRecorder = new MediaRecorder(stream);
                audioChunks = [];
                
                mediaRecorder.ondataavailable = (event) => {
                    audioChunks.push(event.data);
                };
                
                mediaRecorder.onstop = () => {
                    recordedBlob = new Blob(audioChunks, { type: 'audio/webm' });
                    showStatus(`Recording complete! Size: ${(recordedBlob.size / 1024).toFixed(2)} KB`, 'success');
                    testBtn.disabled = false;
                    stream.getTracks().forEach(track => track.stop());
                };
                
                mediaRecorder.start();
                recordBtn.disabled = true;
                stopBtn.disabled = false;
                testBtn.disabled = true;
                showStatus('🔴 Recording... Speak now!', 'info');
                recordBtn.classList.add('recording');
            } catch (error) {
                showStatus(`Error: ${error.message}`, 'error');
                console.error('Error accessing microphone:', error);
            }
        });

        stopBtn.addEventListener('click', () => {
            if (mediaRecorder && mediaRecorder.state !== 'inactive') {
                mediaRecorder.stop();
                recordBtn.disabled = false;
                stopBtn.disabled = true;
                recordBtn.classList.remove('recording');
            }
        });

        testBtn.addEventListener('click', async () => {
            if (!recordedBlob) {
                showStatus('No recording available!', 'error');
                return;
            }

            showStatus('Processing audio...', 'info');
            testBtn.disabled = true;

            try {
                const formData = new FormData();
                formData.append('audio_file', recordedBlob, 'recording.webm');

                const response = await fetch('/api/test/transcribe', {
                    method: 'POST',
                    body: formData
                });

                const result = await response.json();

                if (result.success) {
                    showStatus('✅ Transcription successful!', 'success');
                    transcriptDiv.textContent = result.transcript || '(No speech detected)';
                    audioInfoDiv.innerHTML = `
                        <strong>Audio Info:</strong><br>
                        Format: ${result.format}<br>
                        Size: ${result.size_bytes} bytes<br>
                        WAV Size: ${result.wav_size_bytes} bytes<br>
                        Saved to: ${result.saved_file || 'N/A'}
                    `;
                    resultDiv.style.display = 'block';
                } else {
                    showStatus(`❌ Error: ${result.error}`, 'error');
                }
            } catch (error) {
                showStatus(`❌ Request failed: ${error.message}`, 'error');
                console.error('Error:', error);
            } finally {
                testBtn.disabled = false;
            }
        });
    </script>
</body>
</html>
    """
    return HTMLResponse(content=html_content)


@router.post("/test/transcribe")
async def test_transcribe_audio(audio_file: UploadFile = File(...)):
    """
    Test endpoint to transcribe uploaded audio
    Saves the audio file for debugging and converts it using wave module
    """
    try:
        # Read the uploaded audio data
        audio_data = await audio_file.read()
        
        print(f"[Test] Received audio file: {audio_file.filename}")
        print(f"[Test] Content type: {audio_file.content_type}")
        print(f"[Test] Size: {len(audio_data)} bytes")
        
        # Save the original file for debugging
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        samples_dir = "audio_samples"
        os.makedirs(samples_dir, exist_ok=True)
        
        original_filename = f"{samples_dir}/original_{timestamp}.webm"
        with open(original_filename, "wb") as f:
            f.write(audio_data)
        print(f"[Test] Saved original audio to: {original_filename}")
        
        # Convert to WAV using wave module (no ffmpeg!)
        try:
            # For WebM audio from browser, we need to extract the PCM data
            # However, WebM is a container format. For the test, let's try direct transcription first
            
            # Try direct transcription with Whisper (it supports webm)
            transcript = await transcribe_audio(audio_data, "audio.webm")
            
            if transcript:
                return {
                    "success": True,
                    "transcript": transcript,
                    "format": "webm",
                    "size_bytes": len(audio_data),
                    "wav_size_bytes": "N/A (direct webm)",
                    "saved_file": original_filename
                }
            
            # If direct transcription fails, we need to convert
            # Since we don't have ffmpeg, we'll just return the error
            return {
                "success": False,
                "error": "Transcription returned empty. WebM might need conversion.",
                "format": "webm",
                "size_bytes": len(audio_data),
                "saved_file": original_filename
            }
            
        except Exception as conversion_error:
            print(f"[Test] Conversion error: {conversion_error}")
            return {
                "success": False,
                "error": f"Conversion failed: {str(conversion_error)}",
                "saved_file": original_filename
            }
        
    except Exception as e:
        print(f"[Test] Error: {e}")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "error": str(e)
        }

