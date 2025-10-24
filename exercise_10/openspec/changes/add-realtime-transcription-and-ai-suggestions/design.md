## Technical Design

### Overview
Implements near real-time audio transcription and agent-only AI suggestions over WebSockets, plus customer context fetching on call start.

### Components
- WhisperService: wraps OpenAI Whisper API calls for audio transcription.
- AIAssistantService: calls LLM to generate structured suggestions.
- WebSocket Router: `/ws/call/{call_id}` routes audio, transcripts, and suggestions between paired participants.
- Customer API: existing endpoints extended to return enriched info for sidebar.

### WebRTC Layer (Guidance)
- Current scope: audio flows via WebSocket bytes; signaling is minimal.
- Future option: add proper WebRTC with ICE negotiation and SDP exchange endpoints (see ARCHITECTURE.md) using aiortc or a managed provider.
- If adopted, use WebSocket signaling for offer/answer and ICE candidates.

### Audio & Transcription
- Input: browser sends audio chunks (WebM/Opus) via WebSocket bytes.
- Chunking: start with fixed-size chunks (100–300ms) for responsiveness.
- Processing: queue chunks, transcribe sequentially to avoid overlapping requests; consider batching small chunks when necessary.
- Whisper API: use OpenAI SDK with file-like objects. Handle timeouts and errors by skipping failed chunks and continuing.
- Optimizations from ARCHITECTURE.md:
  - VAD (Voice Activity Detection) to avoid silence
  - Optional buffering: 3–5s before STT for accuracy vs. latency tradeoff
  - Parallelism: transcribe one chunk while recording the next

### Suggestions
- Trigger: on customer transcript messages.
- Prompt: system prompt with policy, context; recent conversation window (last N messages).
- Rate limiting: debounce suggestion calls (e.g., 500–1000ms) to avoid flooding on rapid transcripts.
- Delivery: send `ai_suggestion` JSON only to agent partner connection.

### Message Schema
- `audio_received`: { type, size, timestamp }
- `transcript`: { type, speaker, text, timestamp }
- `ai_suggestion`: { type, suggestion, confidence, timestamp }
- `call_started` / `call_ended`: lifecycle events

### Routing & Pairing
- Maintain `active_connections: Dict[str, WebSocket]` keyed by `call_id`.
- Pair via `active_calls` mapping: `{ agent_call_id, customer_call_id }`.
- Forward transcripts (and selected audio) to partner when connected.

### Context Manager (Guidance)
- Maintain per-call state: customer_id, customer_info, last N transcript segments, topics, entities, sentiment, and used suggestions.
- Provide `get_context_for_ai()` to compose a concise context window (customer summary + last 10 turns + topics).
- Use as prompt basis for the AIAssistantService to improve relevance.

### Error Handling & Resilience
- WebSocket loop: catch exceptions per-iteration; on disconnect, cleanup connection state.
- Transcription/AI errors: log, send non-blocking status or fallback suggestion; continue stream.
- Backpressure: if processing lags, drop oldest audio chunk or coalesce; avoid blocking the event loop.

### Configuration
- Env vars: `OPENAI_API_KEY`, `SECRET_KEY`, `DATABASE_URL`, `REDIS_URL`, `CORS_ORIGINS`.
- Next.js rewrite proxies `/api/*` to backend; `NEXT_PUBLIC_WS_URL` for WebSocket.

### Latency Targets
- Transcription: <= 2s from audio receipt to transcript message.
- Suggestions: <= 1s after transcript (debounced).
 - Advanced target (Level 3): transcription < 500ms with streaming STT (e.g., Deepgram live).

### Security & Privacy
- JWT-based auth for protected endpoints.
- Do not persist raw audio by default; recordings configurable and protected.

### STT Options
- Option A: OpenAI Whisper (batch/near-real-time) — simpler integration; workable for <=2s target.
- Option B: Deepgram streaming — recommended for sub-500ms targets; supports interim results.
