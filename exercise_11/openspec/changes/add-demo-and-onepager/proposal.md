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

## Implementation Status
✅ **Documentation Complete** - Demo script and one-pager completed
- **Demo Script**: Complete 3-flow script with narration, timing, and highlight points (~2 minutes total)
  - Flow 1: Medical refusal with empathy and resources
  - Flow 2: Evidence-based advice with citations and streaming
  - Flow 3: Crisis detection and HITL escalation
- **One-Pager**: Executive summary with actual metrics (500 words)
  - Key Metrics: p95 latency (4.36s), failure rate (0.02%), citation rate (90%+)
  - Safety & Quality: Guardrails, crisis detection (316ms), HITL queue
  - Key Risks: Cost escalation, RAG coverage, crisis latency, hallucinations
  - Next Steps: Alpha test, beta launch, lite mode, admin dashboard

**Note**: Video recording and distribution tasks are deferred as they require manual recording/editing work. Documentation is production-ready for live demos.

