## ADDED Requirements

### Requirement: Dual AI Suggestion Approach
The system SHALL provide two distinct AI suggestion approaches: real-time suggestions for chat messages and periodic/batch suggestions for voice transcriptions, with unified presentation in the AI suggestion panel.

#### Scenario: Real-Time Chat Suggestions
- **WHEN** a chat message is received from the customer
- **THEN** the backend immediately generates an AI suggestion for the agent
- **AND** sends an `ai_suggestion` message only to the agent partner with `source: "realtime"`
- **AND** the suggestion appears in the unified AI suggestion panel

#### Scenario: Periodic Voice Transcription Suggestions
- **WHEN** voice transcriptions accumulate over the configured time window (default: 5 minutes)
- **THEN** the backend generates comprehensive AI suggestions for the agent
- **AND** sends `ai_suggestion` messages only to the agent partner with `source: "batch"`
- **AND** the suggestions appear in the unified AI suggestion panel

#### Scenario: AI Suggestion Panel Management
- **WHEN** AI suggestions exceed the configured maximum (environment variable `MAX_AI_SUGGESTIONS=10`)
- **THEN** the system implements FIFO rotation to maintain panel limits
- **AND** clearly labels each suggestion with its source (`realtime` vs. `batch`)

### Requirement: Unified Conversation Context for AI
The system SHALL provide a unified conversation context that combines both chat messages and voice transcriptions for comprehensive AI analysis.

#### Scenario: Context Composition for Real-Time Suggestions
- **WHEN** generating real-time AI suggestions for chat messages
- **THEN** the backend composes a context including recent chat history and voice transcriptions
- **AND** maintains chronological order with precise timestamps
- **AND** sends this context to the LLM for relevant suggestions

#### Scenario: Context Composition for Batch Suggestions
- **WHEN** generating periodic AI suggestions for voice transcriptions
- **THEN** the backend composes a comprehensive context including all recent conversation elements
- **AND** maintains chronological order with precise timestamps
- **AND** implements token-aware content management to prevent oversized inputs

#### Scenario: Context Window Management
- **WHEN** the conversation context approaches LLM token limits
- **THEN** the system automatically summarizes older content
- **AND** maintains focus on recent, relevant conversation elements
- **AND** preserves timestamp accuracy for audit trail