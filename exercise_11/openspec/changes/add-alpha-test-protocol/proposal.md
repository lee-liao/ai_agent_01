# Add Alpha Test Protocol

## Why
Before broader release, the Child Growth Assistant needs real user validation. An alpha test with parents ensures the system is helpful, safe, and meets user needs. Structured feedback collection identifies critical issues early.

## What Changes
- Create alpha test plan document (`docs/alpha_plan.md`)
- Write consent copy explaining AI limitations and data usage
- Build feedback form for testers
- Set up issue logging system
- Target: ≥80% "felt helpful" rating, 0 P0 safety bugs

## Impact
- Affected specs: New capability `alpha-testing`
- Affected code:
  - `docs/alpha_plan.md` - Test plan and procedures
  - `docs/alpha_consent.md` - Consent form copy
  - `frontend/src/app/feedback/page.tsx` - Feedback form UI
  - `backend/app/api/feedback.py` - Feedback submission endpoint
  - `backend/app/models/feedback.py` - Feedback data models
  - `docs/alpha_issues.md` - Issue log template

