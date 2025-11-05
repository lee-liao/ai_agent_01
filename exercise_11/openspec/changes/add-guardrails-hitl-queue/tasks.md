# Implementation Tasks

## 1. Enhanced Guardrails
- [x] 1.1 Add PII detection (names, SSN, addresses, phone numbers)
- [x] 1.2 Add crisis keywords (suicide, abuse, harm) - already existed, enhanced
- [x] 1.3 Add medical symptom detection - already existed
- [ ] 1.4 Implement confidence scoring (deferred - using boolean detection for now)
- [ ] 1.5 Test classification accuracy (manual testing required)

## 2. HITL Queue Backend
- [x] 2.1 Create data models for HITL cases (in-memory dict structure)
- [x] 2.2 Implement `/api/hitl/queue` endpoint (list pending)
- [x] 2.3 Implement `/api/hitl/{id}` endpoint (get case)
- [x] 2.4 Implement `/api/hitl/{id}/reply` endpoint (mentor reply)
- [x] 2.5 Add case status tracking (pending, in_progress, resolved)

## 3. Queue Routing
- [x] 3.1 Modify WebSocket handler to detect HITL triggers
- [x] 3.2 Create case in HITL queue
- [x] 3.3 Send holding message to parent
- [x] 3.4 Route mentor response back to parent chat (via SSE real-time delivery)
- [x] 3.5 Measure routing latency (<500ms) - implemented, manual testing required

## 4. Mentor UI
- [x] 4.1 Create queue list page at `/hitl/queue`
- [x] 4.2 Display pending cases with priority
- [x] 4.3 Create case detail page at `/hitl/case/[id]`
- [x] 4.4 Show full conversation history
- [x] 4.5 Add response textarea and submit button
- [x] 4.6 Implement real-time updates (SSE-based, no polling/flashing)

## 5. Testing
- [ ] 5.1 Test PII detection with sample data (manual testing required)
- [ ] 5.2 Test crisis routing end-to-end (manual testing required)
- [ ] 5.3 Verify mentor reply appears in parent chat (manual testing required)
- [ ] 5.4 Measure routing latency (manual testing required)
- [ ] 5.5 Assert <500ms from trigger to queue creation (manual testing required)

