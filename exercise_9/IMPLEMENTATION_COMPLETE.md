# Exercise 9 Implementation Summary

This document summarizes the work completed across the Exercise 9 plan, with pointers for validation and screenshots to capture.

## 1) Setup & Verification
- Backend and frontend run locally.
- Pages verified: `/`, `/documents`, `/review`, `/chat`, `/hitl`, `/redteam`, `/audit`, `/reports`.

## 2) Pipeline Analysis
- Flow: Classifier → Extractor → Reviewer → Drafter (see `backend/app/agents/pipeline.py`).
- HITL triggers at Extractor (PII), Reviewer (high-risk items), Drafter (final approval).

## 3) Baseline PII Tests
- Sample doc: `data/sample_documents/pii_baseline_test.md`.
- Modes: mask, generalize, refuse (policy controlled).

## 4) Passport PII Pattern
- Added pattern in `extractor.py` and redaction keeps last 4.

## 5) Custom Policy
- External Sharing Policy enforced in Reviewer for third-party mentions.

## 6) Chat Security Hardening
- `chatbot.py` detects injection/exfiltration/encoding; blocks and logs.

## 7) Red Team Tests
- `redteam.py` suite + scenarios; audit logs for events.

## 8) High-Value HITL Trigger
- Reviewer emits `financial_amount` high-risk items for amounts over threshold.
- Pipeline pauses and enqueues HITL.

## 9) Context-Aware PII Heuristics
- Names/emails gain `confidence`; low-confidence names dropped.
- HITL considers confidence thresholds.
- Sample doc: `data/sample_documents/context_pii_test.md`.

## 10) Custom Feature (Export Viewers)
- Redline viewer: `/export/<run_id>/redline`.
- Final viewer: `/export/<run_id>/final`.
- Quick links on Review page when run completes.

## 11) KPIs & Exports Validation
- `/reports` shows metrics from `/api/reports/kpis`.
- Export endpoints validated.

## 12) Documentation & Screenshots
- Update `README.md` and `PIPELINE_NOTES.md` with usage and notes.
- Suggested screenshots:
  - Review page with agent cards and HITL banner
  - HITL queue item details and approval
  - Reports dashboard
  - Redline and Final export pages

## Appendix
- Commits reference:
  - Step 8: High-Value HITL Trigger
  - Step 9: Context-Aware PII Heuristics (plus validation notes)
  - Step 10: Export viewers
  - Review UX improvements (auto-polling, quick links, helper text)
