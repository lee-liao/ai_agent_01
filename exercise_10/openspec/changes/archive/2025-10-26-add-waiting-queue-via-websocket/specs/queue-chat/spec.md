## ADDED Requirements

### Requirement: Agent Chat Use Cases & States
- The system SHALL support the following agent states: Logged In (no chat), In Conversation, Conversation Ended, Logged Out.
- The system SHALL allow a user to login as an agent in the call center.
- The Call Center page SHALL show a “Waiting Customers” queue at the top-right panel.
- The queued customer chat requests SHALL be synchronized with the backend using WebSocket.
- If the agent clicks “Start Chat”, the top queued request in “Waiting Customers” SHALL be picked up and a conversation established.
- When a conversation is established, the previous chat history SHALL be cleared.
- The matched customer context SHALL be shown in the “Customer Info” panel.
- The “Waiting Customers” queue SHALL stay visible (collapsed) showing the current count in the queue.
- The queue SHALL be maintained in Redis in FIFO order.
- After the agent clicks “End Chat”, the conversation SHALL be ended, if still active.

#### Scenario: Agent Monitor Mode
- WHEN the agent opens the Call Center page and is not in a chat
- THEN the “Waiting Customers” queue panel is visible and synchronized via WebSocket

#### Scenario: Agent Take Top (Top of Queue)
- WHEN the agent clicks “Start Chat”
- THEN the top queued customer is picked up and a conversation is established
- AND prior chat history is cleared and customer context is shown

#### Scenario: Agent End Chat
- WHEN the agent clicks “End Chat” while active
- THEN the conversation is ended and state transitions to Conversation Ended

### Requirement: Customer Chat Use Cases & States
- The system SHALL support the following customer states: Not Connected (no request, no conversation), Request Sent (queued), In Conversation, Conversation Ended, Logged Out.
- The context of the customer SHALL be shown in the “Your Info” panel.
- After login, the chat page SHALL be in the “Not Connected” state; login does not enqueue a request.
- After clicking “Chat for Assistance”, the request SHALL be added to the “Waiting Customers” queue.
- The system SHALL allow multiple logins, but only one active “Chat for Assistance” conversation per customer.
- After an agent picks up a request, the queued request SHALL be removed and a conversation established.
- After the customer clicks “End Chat”, if a conversation exists, it SHALL be ended.
- After the customer clicks “End Chat” when no conversation exists, the queued request SHALL be removed.
- After the customer clicks “Exit”, if a queued request exists, it SHALL be removed.

#### Scenario: Customer Not Connected After Login
- WHEN the customer logs in
- THEN the page shows “Not Connected” and does not enqueue a request

#### Scenario: Customer Enqueues Assistance Request
- WHEN the customer clicks “Chat for Assistance”
- THEN the queued request is added to “Waiting Customers”

#### Scenario: Customer Conversation Establishment
- WHEN an agent picks up the request
- THEN the conversation is established and the queued request is removed

#### Scenario: Customer End Chat
- WHEN the customer clicks “End Chat”
- THEN if a conversation exists it is ended; if not, the queued request is removed

### Requirement: Queue & Concurrency
- The queue SHALL be FIFO and persisted in Redis.
- Concurrent pickup SHALL be safe: exactly one agent can successfully pick up a customer; other agents attempting to pick up the same customer will fail.

#### Scenario: Concurrent Pickup
- GIVEN two agents, Agent A and Agent B, are viewing the same waiting customer
- WHEN Agent A clicks "Start Chat"
- AND Agent B clicks "Start Chat" a moment later
- THEN Agent A's request succeeds and a conversation is established
- AND Agent B's request fails with an error indicating the customer is no longer available.
