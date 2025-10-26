## ADDED Requirements

### Requirement: Customer Web Page (Chat/Call)
The system SHALL provide a customer-facing web page to start a support session, exchange messages, and optionally capture audio.

#### Scenario: Customer Starts a Session
- WHEN a customer visits the customer page and enters basic info
- THEN the app stores session info locally and navigates to the chat page

#### Scenario: Connects to Agent via WebSocket
- WHEN the customer starts a call
- THEN the app calls `/api/calls/start` with `user_type=customer`
- AND opens a WebSocket to `/ws/call/{call_id}`
- AND sends a `start_call` message to confirm readiness

#### Scenario: Send and Receive Transcripts
- WHEN the customer sends a message
- THEN the app sends a JSON payload `{ type: 'transcript', speaker: 'customer', text }`
- AND displays agent messages of type `transcript` with `speaker='agent'`

#### Scenario: Optional Audio Capture
- GIVEN a microphone is available and permission is granted
- WHEN the customer enables audio
- THEN the app captures and streams audio chunks over WebSocket bytes

#### Scenario: End Session
- WHEN the customer ends the session
- THEN the app sends `{ type: 'end_call' }` and closes the WebSocket

## ADDED Requirements

### Requirement: Unified Styling With Call Center UI
The customer web pages SHALL use the same design system and visual language as the agent Call Center UI.

#### Scenario: Shared Theme Tokens
- GIVEN Tailwind theme tokens in `tailwind.config.js`
- WHEN rendering customer pages
- THEN colors, typography, and spacing use the shared tokens (e.g., `primary.*`), not ad-hoc inline styles

#### Scenario: Consistent Components
- GIVEN common UI patterns (headers, buttons, cards)
- WHEN rendering customer pages
- THEN components match the agent UI style (rounded, shadows, icon set) for a cohesive look

#### Scenario: Brand Consistency
- WHEN viewing customer vs agent pages
- THEN primary color, typography scale, and iconography are consistent across both experiences
