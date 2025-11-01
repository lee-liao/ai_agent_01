# Implementation Tasks

## 1. Documentation
- [ ] 1.1 Create `docs/safety_scope.md` with in-scope and out-of-scope topics
- [ ] 1.2 Document escalation procedures
- [ ] 1.3 Define refusal response templates

## 2. Configuration
- [ ] 2.1 Create `config/safety_policy.json` with classification rules
- [ ] 2.2 Define keyword lists for medical/crisis/legal/therapy topics
- [ ] 2.3 Add confidence thresholds for classification

## 3. Backend Implementation
- [ ] 3.1 Create `backend/app/guardrails.py` with `SafetyGuard` class
- [ ] 3.2 Implement `classify_request()` method
- [ ] 3.3 Implement `get_refusal_template()` method
- [ ] 3.4 Integrate guard hook in WebSocket handler
- [ ] 3.5 Add logging for flagged requests

## 4. Testing
- [ ] 4.1 Create `backend/tests/test_guardrails.py`
- [ ] 4.2 Write 20 red-team prompts (5 medical, 5 crisis, 5 legal, 5 therapy)
- [ ] 4.3 Assert correct classification and refusal templates
- [ ] 4.4 Test edge cases and borderline prompts
- [ ] 4.5 Verify pass rate: 100% of out-of-scope prompts trigger refusal

