# Implementation Tasks

## 1. Enhanced Guardrails
- [ ] 1.1 Add PII detection (names, SSN, addresses, phone numbers)
- [ ] 1.2 Add crisis keywords (suicide, abuse, harm)
- [ ] 1.3 Add medical symptom detection
- [ ] 1.4 Implement confidence scoring
- [ ] 1.5 Test classification accuracy

## 2. HITL Queue Backend
- [ ] 2.1 Create data models for HITL cases
- [ ] 2.2 Implement `/api/hitl/cases` endpoint (list pending)
- [ ] 2.3 Implement `/api/hitl/cases/{id}` endpoint (get case)
- [ ] 2.4 Implement `/api/hitl/cases/{id}/respond` endpoint (mentor reply)
- [ ] 2.5 Add case status tracking (pending, in_progress, resolved)

## 3. Queue Routing
- [ ] 3.1 Modify WebSocket handler to detect HITL triggers
- [ ] 3.2 Create case in HITL queue
- [ ] 3.3 Send holding message to parent
- [ ] 3.4 Route mentor response back to parent chat
- [ ] 3.5 Measure routing latency (<500ms)

## 4. Mentor UI
- [ ] 4.1 Create queue list page at `/hitl/queue`
- [ ] 4.2 Display pending cases with priority
- [ ] 4.3 Create case detail page at `/hitl/case/[id]`
- [ ] 4.4 Show full conversation history
- [ ] 4.5 Add response textarea and submit button
- [ ] 4.6 Implement real-time updates (new cases)

## 5. Testing
- [ ] 5.1 Test PII detection with sample data
- [ ] 5.2 Test crisis routing end-to-end
- [ ] 5.3 Verify mentor reply appears in parent chat
- [ ] 5.4 Measure routing latency
- [ ] 5.5 Assert <500ms from trigger to queue creation

