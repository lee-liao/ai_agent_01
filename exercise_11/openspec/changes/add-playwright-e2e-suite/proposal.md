# Add Playwright E2E Test Suite

## Why
Comprehensive end-to-end tests ensure the entire user journey works correctly, including UI interactions, WebSocket communication, and response quality. Prevents regressions and validates acceptance criteria.

## What Changes
- Expand `frontend/e2e/assistant.spec.ts` to ≥10 realistic scenarios
- Cover normal advice, refusal flow, HITL escalation, citations
- Assert response structure (empathy, 3 steps, citation, safety footer)
- All scenarios must pass (green)

## Impact
- Affected specs: New capability `e2e-testing`
- Affected code:
  - `frontend/e2e/assistant.spec.ts` - E2E test scenarios
  - `frontend/playwright.config.ts` - Test configuration
  - `backend/tests/fixtures.py` - Test data fixtures

