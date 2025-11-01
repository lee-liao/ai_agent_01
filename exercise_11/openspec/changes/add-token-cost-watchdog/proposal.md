# Add Token/Cost Watchdog

## Why
OpenAI API costs can escalate quickly. Token tracking, budget caps, and "lite mode" fallback ensure cost control while maintaining service availability.

## What Changes
- Create `billing/ledger.py` to track per-turn tokens and costs
- Implement budget caps and "lite mode" fallback (smaller model)
- Generate nightly CSV reports
- Add admin dashboard with cost sparklines
- Over-budget requests return lite mode with user notice

## Impact
- Affected specs: New capability `cost-management`
- Affected code:
  - `billing/ledger.py` - Token and cost tracking
  - `billing/reports.py` - Daily report generation
  - `backend/app/config.py` - Budget configuration
  - `backend/app/llm.py` - Lite mode fallback logic
  - `frontend/src/app/admin/costs/page.tsx` - Admin dashboard
  - `backend/app/api/admin.py` - Cost API endpoints

