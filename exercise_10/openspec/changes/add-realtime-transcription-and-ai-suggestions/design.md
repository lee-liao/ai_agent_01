## Technical Design

### Overview
Implements accurate audio transcription with smart chunking and batch AI suggestions over WebSockets, plus customer context fetching on call start. Differentiates between real-time chat suggestions and periodic voice transcription analysis.

### Components
- WhisperService: wraps OpenAI Whisper API calls for audio transcription with smart chunking.
- AIAssistantService: calls LLM to generate structured suggestions with different timing strategies.
- WebSocket Router: `/ws/call/{call_id}` routes audio, transcripts, and suggestions between paired participants.
- Customer API: existing endpoints extended to return enriched info for sidebar.

### WebRTC Layer (Guidance)
- Current scope: audio flows via WebSocket bytes; signaling is minimal.
- Future option: add proper WebRTC with ICE negotiation and SDP exchange endpoints (see ARCHITECTURE.md) using aiortc or a managed provider.
- If adopted, use WebSocket signaling for offer/answer and ICE candidates.

### Audio & Transcription Strategy
**Smart Chunking Approach:**
- Input: browser sends audio chunks (WebM/Opus) via WebSocket bytes.
- Chunking: Intelligent 5-10 second chunks based on natural speech boundaries with precise timestamps.
- Pause Detection: Energy-based VAD to identify speech vs. silence for optimal chunk boundaries.
- Processing: Queue chunks, transcribe with timestamps preserved for audit trail accuracy.
- Whisper API: use OpenAI SDK with file-like objects. Handle timeouts and errors gracefully.
- Timestamps: Each transcription segment maintains precise timing for audit and synchronization.

**Optimizations:**
- Preserve timestamp accuracy on granular chunks for better audit trail
- Energy-based VAD for natural speech boundaries
- Configurable chunk sizes via environment variables
- Graceful error handling with fallback mechanisms

### AI Suggestions Strategy
**Dual Approach for Different Use Cases:**
1. **Chat Messages**: Immediate AI suggestions (real-time) for instant agent support
2. **Voice Transcriptions**: Periodic/batch AI suggestions for comprehensive conversation analysis

**Processing Windows:**
- Configurable time windows via `CONTEXT_WINDOW_MINUTES` environment variable (default: 5 minutes)
- Prevent oversized LLM inputs with automatic content limiting
- Maintain rolling context for relevance with token-aware processing

### Unified Conversation Timeline
**Integration of Multiple Input Sources:**
- Chat messages and voice transcriptions both maintain precise timestamps
- Seamless merging of chronological chat history + transcriptions for LLM processing
- Context preservation regardless of input method (voice vs. text)

### Message Schema
- `audio_received`: { type, size, timestamp }
- `transcript`: { type, speaker, text, timestamp }
- `ai_suggestion`: { type, suggestion, confidence, timestamp, source: "realtime"|"batch" }
- `call_started` / `call_ended`: lifecycle events

### Routing & Pairing
- Maintain `active_connections: Dict[str, WebSocket]` keyed by `call_id`.
- Pair via `active_calls` mapping: `{ agent_call_id, customer_call_id }`.
- Forward transcripts (and selected audio) to partner when connected.

### Context Manager
**Temporary In-Memory Context (Current Stage):**
- Maintain per-call state: customer_id, customer_info, conversation segments, topics, entities
- Provide `get_context_for_ai()` to compose chronological context (chat + transcriptions)
- Unified timeline combining both voice and text inputs with precise timestamps
- Session-bound context (lost when call ends) - preparing for future persistence

### AI Suggestion Panel Management
**Configurable Limits:**
- Environment variable `MAX_AI_SUGGESTIONS=10` (default) to prevent panel overload
- FIFO rotation when exceeding limit
- Clear labeling of suggestion sources (Real-time vs. Batch/Periodic)
- Unified panel for both chat and voice suggestions

### Error Handling & Resilience
- WebSocket loop: catch exceptions per-iteration; on disconnect, cleanup connection state.
- Transcription/AI errors: log, send non-blocking status or fallback suggestion; continue stream.
- Backpressure: if processing lags, drop oldest chunks or coalesce; avoid blocking the event loop.

### Configuration
**Environment Variables:**
```bash
# Processing intervals
CONTEXT_WINDOW_MINUTES=5        # Periodic LLM processing window
MAX_AI_SUGGESTIONS=10           # Maximum items in suggestion panel

# Chunking parameters  
VOICE_CHUNK_SECONDS=5          # Base audio chunk size
PAUSE_DETECTION_THRESHOLD=0.8  # Silence threshold (0.0-1.0)

# API Keys
OPENAI_API_KEY=                # Required for Whisper and GPT
SECRET_KEY=                    # JWT signing
DATABASE_URL=                  # Future: for persistent context
REDIS_URL=                     # Queue management
CORS_ORIGINS=                  # CORS configuration
```

### Latency & Accuracy Targets
- Transcription: <= 2s from audio end to transcript availability (batch processing acceptable)
- Chat Suggestions: <= 1s for real-time support
- Voice Analysis: Configurable intervals (default: 5 minutes) for comprehensive insights
- Timestamp Accuracy: Millisecond precision for audit trail

### Security & Privacy
- JWT-based auth for protected endpoints.
- Do not persist raw audio by default; recordings configurable and protected.
- Secure handling of customer context and conversation data.

### STT Options
- Option A: OpenAI Whisper (batch/near-real-time) — simpler integration; workable for current scope.
- Option B: Deepgram streaming — future enhancement for sub-500ms targets; supports interim results.
