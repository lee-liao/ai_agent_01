# Exercise 10 – Implementation Plan

## Goals
- Deliver a real-time AI Call Center Assistant with audio streaming, live transcription, and AI suggestions.
- Meet acceptance criteria for streaming chat, session restore, authentication, and package quality where applicable.
- Keep scope pragmatic: build on existing scaffolds and wire missing pieces incrementally.

## Current State (scanned)
- Backend (FastAPI)
  - `exercise_10/backend/app/main.py`: App wiring, CORS, routers, health endpoints.
  - `exercise_10/backend/app/api/calls.py`: In-memory call matching and status (agent/customer). Endpoints: `/api/calls/start`, `/api/calls/status/{id}`, `/api/calls/end/{id}`, `/api/calls/stats`, `/api/calls/match/{id}`.
  - `exercise_10/backend/app/api/websocket.py`: WebSocket `/ws/call/{call_id}`; accepts bytes (audio) and JSON (control/transcript). Echoes `audio_received`, forwards audio bytes and transcript to partner if matched.
  - Placeholders for DB (`models.py`, `database.py`) and auth (`auth.py`). No STT or AI logic yet.
- Frontend (Next.js)
  - Pages: `frontend/src/app/calls/page.tsx` (agent console), `frontend/src/app/customer/page.tsx` (customer signin), `frontend/src/app/customer/chat/page.tsx` (customer chat UI).
  - Lib: `frontend/src/lib/audioUtils.ts` (mic access, MediaRecorder, playback, visualization), `frontend/src/lib/useAudioCall.ts` (hook to capture and send audio chunks via WS, audio level).
  - UI supports text transcripts over WS; audio forwarding/playback wiring is not complete yet.
- Docs
  - `QUICK_REFERENCE.md`, `ARCHITECTURE.md`, `STUDENT_TASKS*.md`, `ADVANCED_REQUIREMENTS.md`, `SETUP.md`, `AUDIO_CALLING_GUIDE.md` describe desired SSE, STT, AI, and production polish.

## Gaps vs Quick Reference
- Speech-to-Text (Whisper/Deepgram) not implemented; no streaming transcripts from audio.
- AI assistant (GPT-4) not implemented; no streaming suggestions.
- SSE endpoints not present; WS used for signaling but not for AI streaming.
- Persistence: active in-memory only; no Postgres models or saving conversations.
- Auth is minimal (localStorage on FE); no backend role enforcement.
- Audio: WS forwards bytes but FE does not play partner audio yet.

## Implementation Phases

1) Environment & Bootstrap
- [ ] Create `.env` from `backend/env.example`; set `OPENAI_API_KEY`, DB and Redis variables.
- [ ] Bring up `docker-compose` services for Postgres and Redis.
- [ ] Verify backend runs on `:8000` and frontend on `:3000`.
- [ ] Smoke test WS connect from agent and customer pages.

2) Call Matching & WebSocket Hardening
- [ ] Validate `/api/calls/start` flow for both roles; ensure `/api/calls/match/{id}` resolves partner.
- [ ] Add WS handshake to confirm partner mapping (or poll `/api/calls/match/{id}` on connect) before routing.
- [ ] Add ping/heartbeat and robust cleanup on disconnect in `backend/app/api/websocket.py`.
- [ ] Unify WS error handling and reconnect strategy on FE; emit clear system messages.

3) Two-way Audio Transport (MVP)
- [ ] On FE, play partner audio when binary WS messages arrive using `playAudioChunk(...)`.
- [ ] Ensure `useAudioCall` sends `Blob` with consistent codec (e.g., `audio/webm;codecs=opus`); document codec expectations.
- [ ] Manual test across two tabs: agent speaks, customer hears (and vice versa).

4) Speech-to-Text Integration
- [ ] Add `backend/app/agents/transcription.py` with a simple adapter (OpenAI Whisper, non-streaming initially).
  - [ ] Buffer short rolling windows (e.g., 2–3s) per `call_id`, submit to STT, emit transcript segments over WS `{type:'transcript', speaker, text}`.
  - [ ] Gate with feature flag `ENABLE_STT` in settings.
- [ ] Upgrade to streaming STT if time permits; consider chunk timestamps for alignment.

5) AI Assistant (Suggestions)
- [ ] Add `backend/app/agents/assistant.py` to consume transcript events and context (customer profile when available).
  - [ ] Use OpenAI Chat Completions; stream tokens for low-latency first token.
- [ ] Stream deltas over WS as `{type:'ai_suggestion', delta|text, done}`; optionally add SSE later at `/sse/call/{id}`.
- [ ] Render live suggestions on FE with smooth animation; implement Stop/Abort to cancel and preserve partial.

6) Persistence & Session Restore
- [ ] Define DB models: Calls, Participants, Messages (speaker, text, timestamps, type=transcript|ai|system). Optionally store audio chunk refs.
- [ ] Write on finalized transcripts and AI completions; store enough to replay.
- [ ] Add REST endpoints to fetch prior conversation by `call_id`; FE hydrates on refresh to avoid duplicates and restore state.
- [ ] Optional: IndexedDB/localStorage backup with conflict resolution.

7) Authentication & Roles
- [ ] Continue FE localStorage gate; add backend middleware to accept simple bearer/header (e.g., `x-role`) and enforce route guards.
- [ ] Stretch: integrate NextAuth on FE and JWT validation on BE; enforce admin vs agent gates server-side.

8) Polish & UX
- [ ] Add customer info panel and quick action buttons.
- [ ] Waveform/level indicators using `AudioVisualizer`.
- [ ] Generate call summary on end (AI prompt), display to agent, persist in DB.
- [ ] Improve accessibility, empty/error states, and loading/progress indicators.

9) Testing & Validation
- [ ] Backend unit tests for call matching and WS handler logic.
- [ ] Integration tests for REST endpoints; manual validation for WS and audio flows.
- [ ] Frontend component tests for chat list and suggestion renderer.
- [ ] Performance checks: first AI token <1s, WS latency stable, audio start <2s.

## Milestones
- [ ] M1: WS chat plus audio forwarding MVP (no STT/AI).
- [ ] M2: STT emits live transcripts to both parties.
- [ ] M3: AI suggestions stream and can be aborted.
- [ ] M4: Persistence with session restore across refresh.
- [ ] M5: Role gates and UX polish.

## Acceptance Alignment
- [ ] Streaming Chat: optimistic echo on FE; backend streams AI deltas; Stop preserves partial.
- [ ] Session Restore: hydrate from DB and avoid duplicates; optional IndexedDB fallback when needed.
- [ ] Authentication: role flags enforced in FE and checked on BE routes.
- [ ] Package Quality: maintain TS types in FE libs; avoid bundling React; Storybook for `packages/agent-ui` if expanded.

## Risks & Notes
- Browser autoplay policies can block audio playback; ensure a user gesture before playing partner audio.
- Opus/webm over WS is demo-friendly but not interoperable with telephony; for production, consider proper WebRTC peer connections.
- STT latency/cost: batch small windows to balance speed and accuracy.
- In-memory state is fine for the lab, but guard with locks or move to Redis if scaling across workers.

## Next Actions
- [ ] Wire partner audio playback on FE and verify two-way audio.
- [ ] Add transcription adapter and emit transcripts over WS.
- [ ] Implement AI suggestion streaming and UI rendering.
- [ ] Define DB models and write paths for transcripts and summaries.
