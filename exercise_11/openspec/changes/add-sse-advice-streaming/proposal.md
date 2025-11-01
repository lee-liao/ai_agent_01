# Add SSE Advice Streaming

## Why
Streaming responses provide better UX by showing partial advice as it's generated, reducing perceived latency. Parents see the assistant "thinking" and get faster feedback.

## What Changes
- Create backend SSE endpoint that streams advice chunks
- Modify LLM integration to stream tokens
- Add frontend SSE consumer in `/coach/chat`
- Display streaming updates in real-time
- Ensure first token arrives <1.5s

## Impact
- Affected specs: New capability `sse-streaming`
- Affected code:
  - `backend/app/api/coach.py` - New SSE endpoint `/api/coach/stream/{session_id}`
  - `backend/app/llm.py` - Streaming LLM calls
  - `frontend/src/app/coach/chat/page.tsx` - SSE consumer
  - `frontend/src/lib/coachApi.ts` - SSE client helper

