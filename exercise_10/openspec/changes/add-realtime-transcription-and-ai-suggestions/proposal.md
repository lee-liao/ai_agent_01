## Why
Core capabilities from exercise_10 are not yet implemented in code: accurate audio transcription (Whisper) with smart chunking and batch AI suggestions. Customer context exists but is not integrated into the call flow. Implementing these unlocks the intended real-time assistant experience with proper timing differentiation.

## What Changes
- Add WhisperService with intelligent audio chunking based on natural speech boundaries
- Add AIAssistantService with dual suggestion approach: real-time for chat, batch for voice
- Wire customer context fetch on call start and display in frontend
- Implement unified conversation timeline with precise timestamps for audit purposes
- Update env/config for API keys, CORS, and new configuration parameters

## Impact
- Backend: `backend/app/api/websocket.py`, new files `backend/app/api/whisper_service.py`, `backend/app/api/ai_service.py`
- Frontend: `frontend/src/app/calls/page.tsx` (display transcripts/suggestions, context, unified timeline)
- Config: `backend/app/config.py` and `.env` for `OPENAI_API_KEY`, `SECRET_KEY`, and new environment variables
- DevOps: `docker-compose.yml` uses `OPENAI_API_KEY` and service ports

## Risks
- Latency/streaming performance; handle backpressure and partial failures
- API quotas and rate limits; add graceful fallback
- Large context windows for LLM processing; implement token-aware content management

## Rollout
- Implement Level 1 tasks first; test end-to-end; then iterate on enhancements (Level 2/3)
- Focus on accurate transcription with smart chunking rather than ultra-low latency
- Prepare foundation for future persistence and call reconnection features

