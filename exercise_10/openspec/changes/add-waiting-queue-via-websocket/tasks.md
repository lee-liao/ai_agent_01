## Implementation Tasks
- [ ] Backend: WebSocket queue sync (subscribe_queue, queue_update, pickup, end_chat), Redis-backed FIFO queue, concurrency safety
- [ ] Frontend (Agent): Monitor queue, Start Chat picks top queued, show customer context, clear history, keep queue visible (collapsed), End Chat
- [ ] Frontend (Customer): Not Connected after login, Chat for Assistance enqueues, prevent multiple active chats, End Chat removes queued/no-conversation item, Exit removes queued item

## Acceptance Criteria (Verify with DevTools)
- [ ] Agent states: Logged In (no chat), In Conversation, Conversation Ended, Logged Out (voice call states planned)
- [ ] Agent sees Waiting Customers (top-right), items sync via WebSocket
- [ ] Start Chat picks top queued and establishes conversation; prior history cleared; Customer Info shows context
- [ ] Waiting Customers remains visible (collapsed) during conversation (shows count)
- [ ] Redis FIFO queue (not required for local demo, but spec requires in production); racing pickup handled
- [ ] End Chat ends active conversation
- [ ] Customer states: Not Connected, Request Sent, In Conversation, Conversation Ended, Logged Out (voice call planned)
- [ ] Login does not enqueue; Chat for Assistance enqueues; one active chat per customer
- [ ] After pickup, queued request removed; End Chat ends or removes queued item appropriately; Exit removes queued item
