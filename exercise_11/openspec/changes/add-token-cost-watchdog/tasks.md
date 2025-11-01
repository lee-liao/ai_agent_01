# Implementation Tasks

## 1. Token Tracking
- [ ] 1.1 Create `billing/ledger.py` module
- [ ] 1.2 Implement `log_usage(session_id, prompt_tokens, completion_tokens, model)`
- [ ] 1.3 Calculate cost based on model pricing
- [ ] 1.4 Store usage records (in-memory or DB)
- [ ] 1.5 Integrate logging in LLM generation

## 2. Budget Caps
- [ ] 2.1 Add `DAILY_BUDGET_USD` to config
- [ ] 2.2 Implement `get_today_spend()` function
- [ ] 2.3 Check budget before LLM calls
- [ ] 2.4 Trigger lite mode when over budget
- [ ] 2.5 Log budget breaches

## 3. Lite Mode Fallback
- [ ] 3.1 Define lite model (e.g., gpt-3.5-turbo vs gpt-4)
- [ ] 3.2 Implement `generate_advice_lite()` function
- [ ] 3.3 Return notice message with response
- [ ] 3.4 Track lite mode usage separately
- [ ] 3.5 Test quality difference

## 4. Reports
- [ ] 4.1 Create `billing/reports.py`
- [ ] 4.2 Implement `generate_daily_report()` function
- [ ] 4.3 Export CSV with: date, sessions, tokens, cost
- [ ] 4.4 Schedule nightly cron job
- [ ] 4.5 Store reports in `billing/reports/` directory

## 5. Admin Dashboard
- [ ] 5.1 Create `/admin/costs` page
- [ ] 5.2 Fetch cost data from backend API
- [ ] 5.3 Display daily spend sparkline chart
- [ ] 5.4 Show current budget utilization
- [ ] 5.5 List top sessions by cost

