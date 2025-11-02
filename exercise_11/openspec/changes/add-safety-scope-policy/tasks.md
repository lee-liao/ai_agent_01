# Implementation Tasks

## 1. Documentation
- [ ] 1.1 Create `docs/safety_scope.md` with in-scope and out-of-scope topics (DEFERRED - minimal demo)
- [ ] 1.2 Document escalation procedures (DEFERRED - minimal demo)
- [x] 1.3 Define refusal response templates (IN guardrails.py)

## 2. Configuration
- [x] 2.1 Create `config/safety_policy.json` with classification rules
- [x] 2.2 Define keyword lists for medical/crisis/legal/therapy topics
- [ ] 2.3 Add confidence thresholds for classification (MINIMAL - keyword-based only)

## 3. Backend Implementation
- [x] 3.1 Create `backend/app/guardrails.py` with `SafetyGuard` class
- [x] 3.2 Implement `classify_request()` method
- [x] 3.3 Implement `get_refusal_template()` method
- [x] 3.4 Integrate guard hook in WebSocket handler (and SSE endpoint)
- [ ] 3.5 Add logging for flagged requests (DEFERRED)

## 4. Testing
- [x] 4.1 Create `backend/tests/test_guardrails.py`
- [x] 4.2 Write 20 red-team prompts (5 medical, 5 crisis, 5 legal, 5 therapy)
- [x] 4.3 Assert correct classification and refusal templates
- [x] 4.4 Test edge cases and borderline prompts
- [x] 4.5 Verify pass rate: 100% of out-of-scope prompts trigger refusal

**Status**: ✅ Minimal implementation complete - 11/16 tasks (core functionality done)  
**Tests**: 24/24 passing  
**Commit**: 469516d

