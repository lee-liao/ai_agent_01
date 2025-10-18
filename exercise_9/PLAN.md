# Exercise 9 Implementation Plan

## Milestones
1. Setup & Verification
2. Pipeline Analysis
3. PII Testing
4. PII Extension (Passport)
5. Custom Policy
6. Chat Security Hardening
7. Red Team Tests
8. HITL Trigger (High-Value)
9. Context-Aware PII
10. Custom Feature
11. KPIs & Export Validation
12. Documentation & Screenshots

## Steps & Deliverables

### 1) Setup & Verification
- Run backend: `uvicorn app.main:app --reload --port 8000` (in `exercise_9/backend`)
- Run frontend: `npm install && npm run dev` (in `exercise_9/frontend`)
- Verify pages: `/`, `/documents`, `/review`, `/chat`, `/hitl`, `/redteam`, `/audit`, `/reports`
- Deliverables: 8 page screenshots, 5 observations, pipeline summary

### 2) Pipeline Analysis
- Read `backend/app/agents/{pipeline.py, classifier.py, extractor.py, reviewer.py, drafter.py}`
- Document agent order, inputs/outputs, HITL points
- Deliverables: Flowchart, agent responsibility table, HITL trigger explanation, run screenshot

### 3) Baseline PII Detection Tests
- Create markdown doc with SSN, email, phone, credit card, address, bank account
- Test `mask`, `generalize`, `refuse` modes
- Deliverables: test doc, results table, analysis of strengths/weaknesses

### 4) Add Passport PII Pattern
- Update `extractor.py` with `"passport": r"\b[A-Z]{2}\d{7}\b"`
- Add redaction: `***` + last 4 digits
- Deliverables: code changes, test doc, screenshot, explanation

### 5) Implement Custom Policy
- Add policy to `DEFAULT_POLICIES` (e.g., External Sharing Policy)
- Enforce in `reviewer.py` (block/require HITL)
- Deliverables: policy visible in `/api/policies`, run behavior verified

### 6) Harden Chat Security Filters
- Enhance `backend/app/agents/chatbot.py` to detect injection, exfiltration, encoding
- Block or sanitize and log security events
- Deliverables: examples of blocked prompts, audit entries

### 7) Add Five Red Team Tests
- Implement tests in `backend/app/agents/redteam.py`
- Add scenarios to `data/test_cases/redteam_scenarios.json`
- Deliverables: code changes, test results, vulnerability report, fix recommendations

### 8) Implement High-Value HITL Trigger
- Detect >$100,000 in `reviewer.py`
- Enqueue HITL in `pipeline.py`, pause and resume on approval
- Deliverables: test doc, HITL queue screenshot, approval screenshots, audit trail

### 9) Context-Aware PII Heuristics
- Reduce false positives for names/emails with contextual rules
- Adjust risk scoring and confidence
- Deliverables: before/after results, rationale

### 10) Custom Feature
- Implement one: clause comparison view / diff export / per-policy KPI
- Deliverables: endpoint(s), UI view, usage notes

### 11) KPIs & Export Validation
- Verify `/api/reports/kpis`, `/api/export/run/{run_id}/redline`, `/api/export/run/{run_id}/final`
- Deliverables: metrics snapshot, export content examples

### 12) Documentation & Screenshots
- Compile findings, screenshots, and instructions
- Deliverables: final report and (optional) short video demo

