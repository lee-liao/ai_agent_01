## Why
The architecture calls for a customer-facing web page. The project has a basic customer flow implemented (sign-in and chat pages), but the capability is not yet captured in specs and is not production-grade. We will formalize the capability and outline enhancements.

## What Changes
- Add capability spec for Customer Web Page: sign-in, start chat, send/receive transcripts, audio capture, end call.
- Define UX flow and WebSocket integration requirements.
- Plan enhancements: auth/session, reconnection, customer context display, and WebRTC signaling migration.

## Impact
- Frontend: `frontend/src/app/customer/page.tsx`, `frontend/src/app/customer/chat/page.tsx` (clarifications and future tasks)
- Backend: alignment with `/api/calls` and `/ws/call/{call_id}` expectations
- Docs: reinforce project conventions and testing guidance

## Risks
- Scope creep into full auth/WebRTC; we’ll separate basic capability from future enhancements.

## Rollout
- Document the current capability and confirm baseline behavior.
- Implement incremental enhancements in follow-up changes.

