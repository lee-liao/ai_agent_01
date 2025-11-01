# Add Guardrails + HITL Queue

## Why
Advanced guardrails detect PII, crisis situations, and medical questions that require human oversight. The HITL (Human-In-The-Loop) queue routes sensitive cases to mentors, ensuring appropriate responses without AI risk.

## What Changes
- Enhance `backend/app/guardrails.py` with PII/crisis/medical classifiers
- Create HITL queue backend API endpoints
- Build HITL UI at `web/app/(hitl)/queue.tsx`
- Crisis prompts route to HITL queue in <500ms
- Mentor replies appear in parent chat seamlessly

## Impact
- Affected specs: Enhance `safety-guardrails`, new capability `hitl-queue`
- Affected code:
  - `backend/app/guardrails.py` - Enhanced classification
  - `backend/app/api/hitl.py` - HITL queue endpoints
  - `backend/app/models/hitl.py` - HITL queue data models
  - `frontend/src/app/(hitl)/queue/page.tsx` - Mentor queue UI
  - `frontend/src/app/(hitl)/case/[id]/page.tsx` - Case detail view
  - `backend/app/api/websocket.py` - HITL message routing

