## ADDED Requirements

### Requirement: Agent Suggestions from AI
The system SHALL generate contextual, actionable suggestions for agents based on customer transcripts.

#### Scenario: Suggestion on Customer Message
- WHEN a customer transcript is received
- THEN the backend requests an AI suggestion
- AND sends an `ai_suggestion` message only to the agent partner

#### Scenario: Fallback on AI Error
- WHEN AI suggestion generation fails
- THEN the backend sends a generic helpful suggestion with reduced confidence

