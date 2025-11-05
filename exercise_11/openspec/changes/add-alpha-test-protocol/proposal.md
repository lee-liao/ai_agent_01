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

## Implementation Status
✅ **Documentation Complete** - 8/30 tasks (22 execution/analysis tasks deferred)
- **Test Plan**: ✅ Comprehensive plan with objectives, scenarios, success criteria
- **Consent Form**: ✅ Detailed form with AI limitations, privacy, opt-out instructions
- **Issue Logging**: ✅ Template with severity levels (P0/P1/P2/P3) and triage process
- **Email Templates**: ✅ Welcome email with variations (initial, reminders, final)

**Key Features**:
- Test objectives: ≥80% helpful rating, 0 P0 safety bugs
- Bug severity levels with response times: P0 (4h), P1 (24h), P2 (1 week), P3 (backlog)
- 5 testing scenarios for testers
- Comprehensive consent form covering AI limitations, data privacy, safety
- Issue tracking template ready for use
- Email communication templates

**Files Created**:
- `docs/alpha_plan.md` - Complete test plan (13 sections)
- `docs/alpha_consent.md` - Consent form with all required disclosures
- `docs/alpha_issues.md` - Issue log template with tracking structure
- `docs/alpha_welcome_email.md` - Email templates for tester communication

**Note**: Execution tasks (feedback form UI, backend API, tester recruitment, actual testing) are deferred until ready to conduct alpha test. All planning documents are production-ready.

