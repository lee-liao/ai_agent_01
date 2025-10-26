## Why
Define authoritative spec for Agent/Customer chat via WebSocket queue with clear states, transitions, and UI behaviors. Replace prior drafts and align implementation to these use cases.

## What Changes
- Agent queue panel synced via WebSocket; Start Chat picks top queued request (FIFO); End Chat ends session.
- Customer login does not enqueue; Chat for Assistance enqueues; multiple logins allowed but single active chat.
- Clear chat history when conversation established; show matched customer context on Agent.
- Keep Waiting Customers visible (collapsed) during conversation; Redis-backed queue with racing pickup safety.

## Impact
- Spec files under `openspec/changes/add-waiting-queue-via-websocket/specs/` and acceptance tasks in `tasks.md`.
- Backend/frontend will be updated to satisfy this spec and verified with DevTools MCP.

## Rollout
- Phase 1: land spec + acceptance criteria.
- Phase 2: implement + verify all use cases using DevTools MCP with two browser instances.
