## Why
Core capabilities from exercise_10 are not yet implemented in code: real-time transcription (Whisper) and AI agent suggestions. Customer context exists but is not integrated into the call flow. Implementing these unlocks the intended real-time assistant experience.

## What Changes
- Add WhisperService and integrate transcription into WebSocket audio pipeline (<= 2s latency target)
- Add AIAssistantService to generate agent-only suggestions based on customer transcripts
- Wire customer context fetch on call start and display in frontend
- Update env/config for API keys and CORS as needed

## Impact
- Backend: `backend/app/api/websocket.py`, new files `backend/app/api/whisper_service.py`, `backend/app/api/ai_service.py`
- Frontend: `frontend/src/app/calls/page.tsx` (display transcripts/suggestions, context)
- Config: `backend/app/config.py` and `.env` for `OPENAI_API_KEY`, `SECRET_KEY`
- DevOps: `docker-compose.yml` uses `OPENAI_API_KEY` and service ports

## Risks
- Latency/streaming performance; handle backpressure and partial failures
- API quotas and rate limits; add graceful fallback

## Rollout
- Implement Level 1 tasks first; test end-to-end; then iterate on enhancements (Level 2/3)

