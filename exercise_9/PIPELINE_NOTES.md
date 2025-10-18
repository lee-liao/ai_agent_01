# Multi-Agent Pipeline Notes

This document summarizes the pipeline flow, inputs/outputs per agent, and HITL interruption points per Exercise 9 Tasks 1–2.

## Flow Overview
1. Classifier → 2. Extractor → 3. Reviewer → 4. Drafter
- Orchestrator: `backend/app/agents/pipeline.py`
- Entry: `/api/run` in `backend/app/main.py` starts `execute_pipeline(...)`

## Agent Responsibilities
- Classifier (`classifier.py`)
  - Input: Raw document content; policies
  - Processing: Doc type detection via regex patterns; sensitivity; financial/health indicators
  - Output: `{ doc_type, sensitivity_level, has_financial_terms, has_health_data, risk_factors, confidence, metadata }`

- Extractor (`extractor.py`)
  - Input: Document, classification, policies
  - Processing: Clause splitting; PII detection via regex; key term extraction; HITL requirement check
  - Output: `{ clauses[], pii_entities[], key_terms[], requires_hitl, extraction_stats }`

- Reviewer (`reviewer.py`)
  - Input: Document, classification, extraction, policies
  - Processing: Clause risk assessment; forbidden advice; missing disclaimers; third-party sharing; overall risk; recommendations; HITL check
  - Output: `{ overall_risk, clause_assessments[], policy_violations[], recommendations[], high_risk_items[], requires_hitl, review_summary }`

- Drafter (`drafter.py`)
  - Input: Document, classification, extraction, review, policies
  - Processing: Apply PII redactions; recommended edits; add disclaimers; generate redline; prepare proposed changes; final HITL check
  - Output: `{ final_document, redline_document, redactions_count, edits_count, disclaimers_added[], proposed_changes[], requires_final_hitl, changes_count, draft_summary }`

## HITL Interruption Points
- After Extractor: if `extraction_result.requires_hitl` → queue HITL, run status `awaiting_hitl`
- After Reviewer: if `review_result.requires_hitl` or `overall_risk == 'high'` → queue HITL, pause
- After Drafter: if `requires_final_hitl` → queue HITL, pause
- Resume: `/api/hitl/{hitl_id}/respond` calls `continue_after_hitl(...)` to proceed to next stage(s)

### High-Value Financial Trigger
- Reviewer now emits explicit HITL items of type `financial_amount` when a clause contains a dollar amount above `Risk Management Thresholds.financial_terms_threshold` (default `$100,000`).
- Each item includes: `clause_id`, `heading`, `amount`, `threshold`, `severity`, and a descriptive message.
- These items appear in `review_result.high_risk_items`, so the pipeline enqueues HITL after the Reviewer stage and pauses the run.

## Finalization
- On completion, run stores `final_output` with `{ document, redactions_count, overall_risk }` and marks status `completed`.

## Notes for Task 8 (High-Value Trigger)
- Implemented explicit high-value HITL items directly in Reviewer clause assessment.
- Amount parsing uses `$[digits,]` with optional cents; threshold is taken from `Risk Management Thresholds` policy.
- Reviewer sets `requires_hitl = True` whenever high-risk items (including high-value) exist; pipeline enqueues HITL.

