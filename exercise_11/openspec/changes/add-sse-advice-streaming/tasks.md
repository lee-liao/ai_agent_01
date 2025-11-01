# Implementation Tasks

## 1. Backend SSE Endpoint
- [ ] 1.1 Create `/api/coach/stream/{session_id}` SSE endpoint
- [ ] 1.2 Implement `StreamingResponse` with `text/event-stream`
- [ ] 1.3 Add session validation and safety checks
- [ ] 1.4 Handle client disconnection gracefully

## 2. LLM Streaming Integration
- [ ] 2.1 Create `backend/app/llm.py` module
- [ ] 2.2 Implement `stream_advice()` function using OpenAI streaming
- [ ] 2.3 Yield tokens as SSE events
- [ ] 2.4 Include metadata (citations, done signal)
- [ ] 2.5 Measure time to first token

## 3. Frontend SSE Consumer
- [ ] 3.1 Create SSE client in `coachApi.ts`
- [ ] 3.2 Handle `EventSource` connection
- [ ] 3.3 Parse SSE events and update UI state
- [ ] 3.4 Display streaming text with typewriter effect
- [ ] 3.5 Handle errors and reconnection

## 4. UX Enhancements
- [ ] 4.1 Show "thinking" indicator before first token
- [ ] 4.2 Animate text appearance
- [ ] 4.3 Disable input during streaming
- [ ] 4.4 Show "done" indicator when complete

## 5. Performance Testing
- [ ] 5.1 Measure time to first token in 10 requests
- [ ] 5.2 Assert p95 < 1.5s
- [ ] 5.3 Test with slow network conditions
- [ ] 5.4 Verify no memory leaks from open SSE connections

