## Design Notes: Customer Web Page

### Styling & Design System
- Use Tailwind theme tokens from `tailwind.config.js` (e.g., `primary.*`) for brand colors.
- Apply consistent component patterns used by the agent UI: rounded cards, subtle shadows, clear iconography.
- Keep typography and spacing scales aligned; avoid ad-hoc inline styles.

### WebSocket Integration
- Calls `_POST /api/calls/start_` then connects to `ws://.../ws/call/{call_id}`.
- Sends `start_call`, `transcript`, and `end_call` messages.
- Displays agent transcripts; handles call lifecycle gracefully.

### Audio Capture
- Optional microphone capture via `useAudioCall` hook; streams audio chunks over WebSocket bytes.
- Shows audio level indicator and mute toggle; device selection when multiple devices available.

### Reconnection
- Basic single retry on `onclose` for better UX; production-grade reconnection can be added later.

### Customer Context
- Initial demo uses `localStorage` for customer info; future enhancement can fetch `/api/customers` for server-side context.
