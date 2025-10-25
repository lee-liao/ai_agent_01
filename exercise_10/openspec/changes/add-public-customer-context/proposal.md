## Why
Customer chat should display real server-side context. Existing customer APIs require agent auth, so the customer UI cannot fetch details. We will add a limited public lookup to power the customer chat info panel.

## What Changes
- Backend: Add a read-only, unauthenticated endpoint to fetch limited customer context (profile + recent orders/tickets) by name/email/phone/account number.
- Frontend: Customer chat pulls server context on connect and displays it in the info panel.

## Impact
- Backend: `backend/app/api/customers.py` (new public search endpoint)
- Frontend: `frontend/src/app/customer/chat/page.tsx` (fetch and render server context)

## Constraints
- Read-only data; no sensitive fields returned.
- Rate-limitable in production (not implemented here).

## Rollout
- Implement endpoint and UI wiring.
- Verify E2E in customer chat.

