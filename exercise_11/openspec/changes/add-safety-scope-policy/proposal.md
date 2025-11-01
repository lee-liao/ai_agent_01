# Add Safety & Scope Policy

## Why
The Child Growth Assistant needs clear boundaries to prevent harmful advice and ensure safe, appropriate responses. Without safety guardrails, the system could provide medical diagnoses, crisis intervention, or other out-of-scope guidance that puts users at risk.

## What Changes
- Create safety policy documentation (`docs/safety_scope.md`)
- Implement machine-readable policy config (`config/safety_policy.json`)
- Add backend guard hook to intercept and classify requests
- Create refusal templates for out-of-scope requests
- Add unit tests for 20 red-team prompts with expected refusals/redirects

## Impact
- Affected specs: New capability `safety-guardrails`
- Affected code:
  - `backend/app/guardrails.py` - New safety checking logic
  - `backend/app/api/websocket.py` - Integration point for guard hook
  - `docs/safety_scope.md` - Policy documentation
  - `config/safety_policy.json` - Configuration
  - `backend/tests/test_guardrails.py` - Unit tests

