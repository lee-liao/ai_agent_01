## Why
The current audio transcription implementation has issues with Whisper API compatibility where audio chunks are sent individually, causing "audio file could not be decoded" errors. The system needs to buffer audio and convert it to compatible formats.

## What Changes
- Add audio buffering mechanism to accumulate audio chunks before processing
- Implement WAV format conversion for Whisper API compatibility
- Update OpenAI library version to improve format support
- Maintain real-time audio forwarding while adding transcription capability

## Impact
- Affected specs: audio-transcription/spec.md
- Affected code: backend/app/api/websocket.py, backend/app/api/whisper_service.py, backend/requirements.txt
- Breaking changes: None, this is an enhancement to existing functionality