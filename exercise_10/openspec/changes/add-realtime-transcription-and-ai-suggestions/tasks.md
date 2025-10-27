## 1. Implementation
- [x] 1.1 Create `backend/app/api/whisper_service.py` with async transcription method
- [x] 1.2 Integrate Whisper into `backend/app/api/websocket.py` for audio -> transcript
- [x] 1.3 Create `backend/app/api/ai_service.py` for suggestions
- [x] 1.4 Generate agent-only suggestions on customer transcript events
- [x] 1.5 Add audio buffering mechanism to improve transcription accuracy and format compatibility
- [x] 1.6 Update OpenAI library version for better format support
- [x] 1.7 Add customer transcript handling to customer chat page
- [ ] 1.8 Enhance customer lookup endpoint and invoke on call start
- [ ] 1.9 Update frontend `src/app/calls/page.tsx` to render transcripts, suggestions, and customer info
- [ ] 1.10 Implement voice call interface specifications (visual indicators, controls)

## 2. Configuration
- [ ] 2.1 Ensure `OPENAI_API_KEY` is read in backend settings
- [ ] 2.2 Confirm CORS and Next.js rewrites support `/api/*`

## 3. Testing
- [ ] 3.1 Manual E2E: customer mic -> transcript < 2s
- [ ] 3.2 Verify agent receives suggestions upon customer speech
- [ ] 3.3 Customer info panel loads on call start

## 4. Documentation
- [ ] 4.1 Update README quickstart for Whisper/GPT and env vars
- [ ] 4.2 Update openspec/project.md if conventions change

