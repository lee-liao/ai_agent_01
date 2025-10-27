# Voice Transcription Implementation Plan

## Problem Statement
The current implementation has issues with audio transcription where:
- Whisper API returns "audio file could not be decoded or its format is not supported" errors
- Audio chunks are sent individually to Whisper, which expects complete files
- WebM format from browser MediaRecorder is not properly handled

## Solution Approach
Implement a buffered audio transcription system following the working example from the reference implementation.

## Technical Requirements
- Use only pip-installable dependencies (no system-level dependencies like FFmpeg)
- Maintain compatibility with existing WebSocket architecture
- Support real-time transcription with minimal latency
- Follow best practices for audio buffering and conversion

## Architecture Changes

### 1. WebSocket Audio Buffering (websocket.py)
- Add per-call audio buffers to accumulate audio chunks
- Implement buffer size threshold (e.g., 5 seconds of audio at 16kHz)
- Batch process audio when buffer threshold is reached
- Continue to forward raw audio to partner in real-time

### 2. Audio Conversion (whisper_service.py)
- Convert accumulated raw PCM audio to WAV format using Python's built-in `wave` module
- Send properly formatted WAV files to Whisper API
- Handle both raw PCM and WebM formats gracefully

### 3. Dependency Updates
- Update OpenAI library to version with better WebM support (1.12.0+)
- Remove unnecessary dependencies

## Implementation Steps

### Step 1: Modify WebSocket Handler
1. Add audio buffering mechanism for each call
2. Implement buffer accumulation logic
3. Process buffered audio in background when threshold reached

### Step 2: Update Whisper Service
1. Implement WAV conversion using Python's wave module
2. Handle both raw PCM and WebM formats
3. Update to newer OpenAI API syntax if needed

### Step 3: Test Integration
1. Test audio buffering functionality
2. Verify transcription quality and timing
3. Ensure real-time audio forwarding still works

## Expected Outcomes
- Eliminate "audio format not supported" errors
- Enable proper real-time transcription
- Maintain audio forwarding for real-time communication
- Reduce dependency requirements

## Success Metrics
- Audio transcription works without format errors
- Minimal latency in transcription (sub 5-second delay)
- Real-time audio forwarding continues to function
- No additional system dependencies required