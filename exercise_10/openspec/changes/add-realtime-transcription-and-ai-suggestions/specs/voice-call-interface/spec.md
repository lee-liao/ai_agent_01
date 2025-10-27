## ADDED Requirements

### Requirement: Voice Call Visual Indicators
The system SHALL provide clear visual feedback during voice calls including audio level meters, voice activity indicators, and transcription displays.

#### Scenario: Audio Level Visualization
- **WHEN** a participant enables voice during a call
- **THEN** a real-time audio level meter is displayed
- **AND** the meter updates continuously to reflect current microphone input

#### Scenario: Voice Connection Status
- **WHEN** voice call is active
- **THEN** the interface shows clear visual indication of active voice connection
- **AND** distinguishes from text-only chat mode

### Requirement: Voice Call States
The system SHALL support multiple voice call states including enabled, disabled, and muted.

#### Scenario: Voice Enabled State
- **WHEN** user clicks "Enable Voice" button
- **THEN** the system activates microphone and shows voice as active
- **AND** audio level visualization becomes available

#### Scenario: Voice Muted State
- **WHEN** user clicks mute toggle during voice call
- **THEN** the system continues recording but indicates muted status
- **AND** microphone input is not processed for transcription

### Requirement: Transcript Display
The system SHALL display transcribed text in the chat interface with proper speaker identification.

#### Scenario: Customer Transcript Display
- **WHEN** customer speech is transcribed
- **THEN** the transcribed text appears in the chat as a customer message
- **AND** the message is clearly identified as originating from the customer

#### Scenario: Agent Transcript Display
- **WHEN** agent speech is transcribed
- **THEN** the transcribed text appears in the chat as an agent message
- **AND** the message is clearly identified as originating from the agent

### Requirement: Voice Call Controls
The system SHALL provide intuitive controls to manage voice calls.

#### Scenario: Enable Voice Control
- **WHEN** user clicks "Enable Voice" button
- **THEN** the system requests microphone access
- **AND** activates voice call functionality

#### Scenario: Mute Toggle Control
- **WHEN** user clicks mute toggle button
- **THEN** the system toggles mute state
- **AND** updates visual indicators accordingly

## MODIFIED Requirements

### Requirement: Real-Time Speech-to-Text Transcription
The system SHALL transcribe incoming audio chunks to text in near real-time and display transcripts in the chat interface.

#### Scenario: Customer Audio Is Transcribed
- **WHEN** the customer sends audio bytes via WebSocket
- **THEN** the backend transcribes the audio to text within 2 seconds
- **AND** sends a `transcript` message with `speaker`, `text`, and `timestamp` back to sender and partner
- **AND** the transcript appears in the chat interface with proper speaker identification

#### Scenario: Audio Buffering and Format Conversion
- **WHEN** audio chunks are received via WebSocket
- **AND** the buffer reaches the threshold (5 seconds of audio)
- **THEN** the system converts the accumulated audio to WAV format
- **AND** sends the WAV file to Whisper API for transcription
- **AND** returns the transcription result to both participants