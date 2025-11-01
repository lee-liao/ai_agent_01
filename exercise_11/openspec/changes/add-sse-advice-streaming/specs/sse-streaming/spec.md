# SSE Streaming Capability

## ADDED Requirements

### Requirement: SSE Endpoint
The system SHALL provide an SSE endpoint for streaming advice responses.

#### Scenario: Successful SSE connection
- **WHEN** client connects to `/api/coach/stream/{session_id}`
- **THEN** the server returns 200 with `text/event-stream` content type
- **AND** keeps connection open for streaming

#### Scenario: Invalid session
- **WHEN** client connects with invalid `session_id`
- **THEN** the server returns 404 error
- **AND** closes the connection

### Requirement: Token Streaming
The system SHALL stream LLM tokens as they are generated.

#### Scenario: Advice token streaming
- **WHEN** the LLM generates advice
- **THEN** each token is sent as an SSE event: `data: {"chunk": "token"}`
- **AND** tokens appear in order

#### Scenario: Stream completion
- **WHEN** the LLM finishes generating
- **THEN** a final event is sent: `data: {"done": true, "citations": [...]}`
- **AND** the SSE connection closes

### Requirement: First Token Latency
The first token SHALL arrive within 1.5 seconds (p95).

#### Scenario: First token timing
- **WHEN** measuring time from request to first token in 10 requests
- **THEN** the p95 latency is <1.5s

### Requirement: Frontend SSE Consumer
The frontend SHALL consume SSE events and display streaming text.

#### Scenario: Real-time text display
- **WHEN** SSE events arrive
- **THEN** the UI appends each chunk to the message
- **AND** displays a typewriter animation effect

#### Scenario: Streaming UI indicators
- **WHEN** streaming is in progress
- **THEN** a "thinking" indicator is shown
- **AND** the input field is disabled
- **AND** a "done" indicator appears when complete

