## Implementation Tasks
- [x] Backend: WebSocket queue sync (subscribe_queue, queue_update, pickup, end_chat), Redis-backed FIFO queue, concurrency safety
- [x] Frontend (Agent): Ready to Assist enables pickup actions; Take Top picks queued (FIFO), show customer context (incl. orders/tickets), clear history, keep queue visible (collapsed), End Chat
- [x] Frontend (Customer): Not Connected after login, Chat for Assistance enqueues, prevent multiple active chats, End Chat removes queued/no-conversation item, Exit removes queued item

## Acceptance Criteria (Verify with DevTools)
- [x] Agent states: Logged In (no chat), In Conversation, Conversation Ended, Logged Out (voice call states planned)
- [x] Agent sees Waiting Customers (top-right), items sync via WebSocket
- [x] Ready to Assist enables Take Top / Pick Up; Take Top picks the next queued customer and establishes conversation; prior history cleared; Customer Info shows context
- [x] Waiting Customers remains visible (collapsed) during conversation (shows count)
- [x] Redis FIFO queue (required in production); racing pickup handled atomically (Lua)
- [x] End Chat ends active conversation; partner receives end state
- [x] Customer states: Not Connected, Request Sent, In Conversation, Conversation Ended, Logged Out (voice call planned)
- [x] Login does not enqueue; Chat for Assistance enqueues; one active chat per customer
- [x] After pickup, queued request removed; End Chat ends or removes queued item appropriately; Exit removes queued item
