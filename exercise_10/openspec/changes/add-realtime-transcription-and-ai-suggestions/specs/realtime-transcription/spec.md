## ADDED Requirements

### Requirement: Real-Time Speech-to-Text Transcription
The system SHALL transcribe incoming audio chunks to text in near real-time and deliver transcripts to both participants.

#### Scenario: Customer Audio Is Transcribed
- WHEN the customer sends audio bytes via WebSocket
- THEN the backend transcribes the audio to text within 2 seconds
- AND sends a `transcript` message with `speaker`, `text`, and `timestamp` back to sender and partner

#### Scenario: Audio Buffering and Format Conversion
- WHEN audio chunks are received via WebSocket
- AND the buffer reaches the threshold (5 seconds of audio)
- THEN the system converts the accumulated audio to WAV format
- AND sends the WAV file to Whisper API for transcription

#### Scenario: Transcription Delivery
- WHEN transcription is successful
- THEN the system sends `transcript` message to both participants
- AND the message includes speaker identification, text content, and timestamp

#### Scenario: Transcription Error Handling
- WHEN transcription fails (API error, invalid audio)
- THEN the backend logs the error and sends a non-blocking status update
- AND continues processing subsequent audio chunks

## MODIFIED Requirements

### Requirement: WebSocket Real-Time Channel
The system SHALL route audio and transcripts between paired participants.

#### Scenario: Route Transcript to Partner
- WHEN a transcript is produced for `call_id`
- THEN the backend forwards it to the partner connection if present

#### Scenario: Route Transcript to Sender
- WHEN a transcript is produced for `call_id`
- THEN the backend sends the transcript to the sender as well as the partner

