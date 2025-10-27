## MODIFIED Requirements
### Requirement: Audio Transcription Processing
The system SHALL buffer audio chunks and convert them to WAV format before sending to Whisper API for transcription.

#### Scenario: Audio buffering and conversion
- **WHEN** audio chunks are received via WebSocket
- **AND** the buffer reaches the threshold (5 seconds of audio)
- **THEN** the system converts the accumulated audio to WAV format
- **AND** sends the WAV file to Whisper API for transcription
- **AND** forwards real-time audio to the partner as before

#### Scenario: Real-time audio forwarding
- **WHEN** audio chunks are received via WebSocket
- **THEN** the system forwards the audio in real-time to the conversation partner
- **AND** simultaneously buffers the audio for transcription processing

### Requirement: Audio Format Compatibility
The system SHALL support audio format conversion to ensure Whisper API compatibility without requiring external dependencies.

#### Scenario: Format conversion using built-in modules
- **WHEN** audio processing is required
- **THEN** the system uses Python's built-in wave module for format conversion
- **AND** no external dependencies like FFmpeg are required