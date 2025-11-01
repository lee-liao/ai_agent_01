# HITL Queue Capability

## ADDED Requirements

### Requirement: PII Detection
The system SHALL detect personally identifiable information in parent messages.

#### Scenario: Name and address detection
- **WHEN** a parent includes "My name is John Smith, I live at 123 Main St"
- **THEN** the message is classified as containing PII
- **AND** routed to HITL queue

### Requirement: Crisis Detection
The system SHALL detect crisis situations requiring immediate human intervention.

#### Scenario: Self-harm indication
- **WHEN** a parent says "I'm afraid I might hurt my child"
- **THEN** the message is classified as crisis
- **AND** routed to HITL queue with high priority

### Requirement: Medical Symptom Detection
The system SHALL detect medical symptoms requiring professional assessment.

#### Scenario: Serious symptom mention
- **WHEN** a parent describes symptoms like "high fever for 5 days"
- **THEN** the message is classified as medical concern
- **AND** routed to HITL queue

### Requirement: Fast Routing
HITL cases SHALL be created within 500ms of detection.

#### Scenario: Routing latency
- **WHEN** a crisis message is detected
- **THEN** the case is created in HITL queue within 500ms
- **AND** the parent receives a holding message

### Requirement: Mentor Queue UI
Mentors SHALL have a queue interface to view and respond to cases.

#### Scenario: Queue list view
- **WHEN** a mentor visits `/hitl/queue`
- **THEN** pending cases are displayed with priority
- **AND** cases show timestamp and category

#### Scenario: Case detail view
- **WHEN** a mentor clicks a case
- **THEN** full conversation history is displayed
- **AND** a response form is available

### Requirement: Response Routing
Mentor responses SHALL appear in the parent's chat seamlessly.

#### Scenario: Mentor reply delivery
- **WHEN** a mentor submits a response
- **THEN** the response is sent to the parent's WebSocket
- **AND** appears in the chat as a message
- **AND** the case is marked resolved

