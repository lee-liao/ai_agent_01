## Why
To improve the quality and reduce the latency of audio calls, we will migrate from a simple WebSocket-based audio streaming solution to a more robust WebRTC-based one. This change also introduces support for call reconnection to improve user experience.

## What Changes
- **BREAKING:** Replace the existing WebSocket audio streaming with a WebRTC peer-to-peer connection.
- Implement a mechanism to maintain per-call state on the server to allow both customers and agents to reconnect to an ongoing call.

## Impact
- Affected specs: `specs/queue-chat/spec.md`
- Affected code: `backend/app/api/websocket.py`, `frontend/src/app/calls/page.tsx`, `frontend/src/app/customer/chat/page.tsx`
