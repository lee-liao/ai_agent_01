## 1. Implementation
- [x] 1.1 Create `backend/app/api/whisper_service.py` with async transcription method
- [x] 1.2 Integrate Whisper into `backend/app/api/websocket.py` for audio -> transcript
- [x] 1.3 Create `backend/app/api/ai_service.py` for suggestions
- [x] 1.4 Generate agent-only suggestions on customer transcript events
- [x] 1.5 Add audio buffering mechanism to improve transcription accuracy and format compatibility
- [x] 1.6 Update OpenAI library version for better format support
- [x] 1.7 Add customer transcript handling to customer chat page
- [x] 1.8 Enhance customer lookup endpoint and invoke on call start
- [x] 1.9 Update frontend `src/app/calls/page.tsx` to render transcripts, suggestions, and customer info
- [x] 1.10 Implement voice call interface specifications (visual indicators, controls)
- [x] 1.11 Implement smart audio chunking with pause detection and precise timestamps
- [x] 1.12 Implement dual AI suggestion approach (real-time for chat, batch for voice)
- [x] 1.13 Implement unified conversation timeline with timestamp synchronization
- [x] 1.14 Add configurable AI suggestion panel limits and FIFO management

## 2. Configuration
- [x] 2.1 Ensure `OPENAI_API_KEY` is read in backend settings
- [x] 2.2 Confirm CORS and Next.js rewrites support `/api/*`
- [x] 2.3 Add new environment variables for chunking and AI suggestion configuration

## 3. Testing
- [x] 3.1 Manual E2E: customer mic -> transcript with accurate timestamps
- [x] 3.2 Verify agent receives real-time suggestions for chat and batch suggestions for voice
- [x] 3.3 Customer info panel loads on call start
- [x] 3.4 Unified conversation timeline maintains proper timestamp synchronization

## 4. Documentation
- [x] 4.1 Update README quickstart for Whisper/GPT and env vars
- [x] 4.2 Update openspec/project.md if conventions change
- [x] 4.3 Document new configuration parameters and their effects

