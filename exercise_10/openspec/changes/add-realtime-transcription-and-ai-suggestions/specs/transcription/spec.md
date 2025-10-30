## ADDED Requirements

### Requirement: Smart Audio Transcription with Natural Speech Boundaries
The system SHALL transcribe incoming audio chunks to text using intelligent chunking based on natural speech boundaries and maintain precise timestamps for audit trail accuracy.

#### Scenario: Customer Audio Is Transcribed with Smart Chunking
- **WHEN** the customer sends audio bytes via WebSocket
- **AND** audio chunks are accumulated based on natural speech boundaries (5-10 seconds or pause detection)
- **THEN** the backend transcribes the accumulated audio to text within 2 seconds
- **AND** sends a `transcript` message with `speaker`, `text`, and precise `timestamp` back to sender and partner

#### Scenario: Audio Processing with Pause Detection
- **WHEN** audio chunks are received via WebSocket
- **AND** energy-based VAD detects a natural pause in speech (0.5-1.0 seconds of silence)
- **THEN** the system processes the accumulated audio segment for transcription
- **AND** maintains millisecond-precision timestamps for audit purposes

#### Scenario: Transcription Error Handling
- **WHEN** transcription fails (API error, invalid audio)
- **THEN** the backend logs the error and sends a non-blocking status update
- **AND** continues processing subsequent audio chunks

### Requirement: Unified Conversation Timeline with Timestamps
The system SHALL maintain a unified conversation timeline that combines both chat messages and voice transcriptions with precise timestamps for audit trail and contextual analysis.

#### Scenario: Chat Message with Timestamp Integration
- **WHEN** a chat message is received from either participant
- **THEN** the system stores the message with precise timestamp in the unified conversation timeline
- **AND** preserves the chronological order with voice transcriptions

#### Scenario: Voice Transcription with Timestamp Integration
- **WHEN** a voice transcription is generated
- **THEN** the system stores the transcription with precise timestamp in the unified conversation timeline
- **AND** preserves the chronological order with chat messages

### Requirement: Periodic AI Analysis of Conversation Context
The system SHALL periodically analyze the accumulated conversation context (both chat and voice) to generate comprehensive insights and suggestions for the agent.

#### Scenario: Periodic Conversation Analysis
- **WHEN** the conversation context exceeds the configured time window (default: 5 minutes)
- **THEN** the system sends the accumulated context to LLM for comprehensive analysis
- **AND** generates actionable suggestions for the agent
- **AND** maintains token-aware content management to prevent oversized inputs

#### Scenario: Configurable Analysis Windows
- **WHEN** environment variable `CONTEXT_WINDOW_MINUTES` is set to a custom value
- **THEN** the system adjusts the periodic analysis interval accordingly
- **AND** maintains the same quality of contextual insights