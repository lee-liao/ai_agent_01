## ADDED Requirements

### Requirement: Agent Chat Use Cases & States
- States: Logged In (no chat), In Conversation, Conversation Ended, Logged Out. Next plan: Voice Call Established, Voice Call Ended.
- Login as an agent in call center.
- The Call Center page shows “Waiting Customers” queue at top-right panel.
- The queued customer chat requests are synchronized with backend using WebSocket.
- If the agent clicks “Start Chat”, the top queued request in “Waiting Customers” is picked up; a conversation is established.
- When the conversation is established, previous chat history is cleared.
- The matched customer context is shown in the “Customer Info” panel.
- The “Waiting Customers” stays visible (collapsed) showing the current count in queue.
- The queue is maintained in Redis in FIFO order; racing pickup by multiple agents is handled.
- After the agent clicks “End Chat”, the conversation is ended, if still active.

#### Scenario: Agent Monitor Mode
- WHEN the agent opens the Call Center page and is not in a chat
- THEN the “Waiting Customers” queue panel is visible and synchronized via WebSocket

#### Scenario: Agent Start Chat (Top of Queue)
- WHEN the agent clicks “Start Chat”
- THEN the top queued customer is picked up and a conversation is established
- AND prior chat history is cleared and customer context is shown

#### Scenario: Agent End Chat
- WHEN the agent clicks “End Chat” while active
- THEN the conversation is ended and state transitions to Conversation Ended

### Requirement: Customer Chat Use Cases & States
- States: Not Connected (no request, no conversation), Request Sent (queued), In Conversation, Conversation Ended, Logged Out. Next plan: Voice Call Established/Ended.
- The context of the customer is shown in the “Your Info” panel.
- After login, the chat page is in “Not Connected”; login does not enqueue.
- After “Chat for Assistance”, the request is added to the “Waiting Customers” queue.
- Multiple logins allowed, but only one active “Chat for Assistance” conversation.
- After pickup, the queued request is removed and a conversation is established.
- After “End Chat”, if a conversation exists, it is ended.
- After “End Chat” when no conversation exists, the queued request is removed.
- After “Exit”, if a queued request exists, it is removed.

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
- Concurrent pickup SHALL be safe: exactly one success; others receive not_found/already_claimed.

