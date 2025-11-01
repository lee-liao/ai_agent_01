# Add Demo and One-Pager Deliverables

## Why
Stakeholders need a quick, reproducible demonstration of the Child Growth Assistant's capabilities and a concise report showing it meets production requirements. This enables decision-making for broader deployment.

## What Changes
- Create 2-minute demo video showing 3 key flows: refusal, normal advice with citations, HITL escalation
- Write one-pager report with metrics: p95 latency, failure rate, citation rate, cost/day, risks, next steps
- Ensure demo is reproducible via `docker compose up`
- Validate metrics align with SLOs

## Impact
- Affected specs: New capability `demo-deliverables`
- Affected code:
  - `docs/demo_script.md` - Demo narration and flow
  - `docs/one_pager.md` - Executive summary report
  - `demo/` - Demo assets (video, screenshots)
  - `scripts/run_demo.sh` - Automated demo setup

