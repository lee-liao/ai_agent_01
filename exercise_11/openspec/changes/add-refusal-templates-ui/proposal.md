# Add Refusal Templates UI Rendering

## Why
Refusal messages need to be supportive and helpful, not cold or dismissive. Parents in difficult situations need empathy and practical resources, not just a "no." Well-designed refusal templates maintain trust while setting boundaries.

## What Changes
- Create supportive refusal copy with empathy statements
- Add resource links (hotlines, professional referrals)
- Implement UI rendering for refusal messages with distinct styling
- All refusals show empathy + clickable resource links
- Test all refusal categories (medical, crisis, legal, therapy)

## Impact
- Affected specs: Enhance `safety-guardrails` capability
- Affected code:
  - `backend/app/guardrails.py` - Enhanced refusal templates
  - `frontend/src/components/RefusalMessage.tsx` - Dedicated refusal UI component
  - `frontend/src/app/coach/chat/page.tsx` - Integration
  - `config/refusal_templates.json` - Template configurations
  - `backend/tests/test_refusal_templates.py` - Unit tests

