## ADDED Requirements

### Requirement: Conversation History Storage
The system SHALL store complete conversation transcripts when a call ends for future reference and quality assurance.

#### Scenario: Save Conversation on Call End
- **WHEN** a call ends (either party disconnects)
- **THEN** the system saves the complete conversation history to the database
- **AND** includes all transcribed messages, timestamps, and participant information

#### Scenario: Retrieve Conversation History
- **WHEN** an agent requests conversation history for a ticket
- **THEN** the system returns all related conversations in chronological order
- **AND** displays message text, speaker, and timestamp for each message

## MODIFIED Requirements

### Requirement: Ticket Association
The system SHALL link conversations to relevant support tickets for continuity.

#### Scenario: Link Conversation to Ticket
- **WHEN** a conversation is saved and a ticket number is available
- **THEN** the system creates a relationship between the conversation and the ticket
- **AND** allows retrieval of the conversation through the ticket interface