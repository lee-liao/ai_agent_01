# Exercise 8: HITL Contract Redlining Orchestrator (Week 5)

This scaffold sets up a legal document review/redlining pipeline with HITL (human-in-the-loop) gates and agentic orchestration.

## What’s included (scaffold)
- Backend (FastAPI): run orchestration, HITL gates, blackboard API, export, reports, replay
- Frontend (Next.js): minimal HITL pages (Risk Gate, Final Gate), Run, Replay, Reports
- Data seeds: sample contracts (Markdown), small policy book JSON, reviewer checklist YAML
- Observability: stub tracing + cost

## Quick start
### Backend
- cd exercise_8/backend
- python -m venv .venv && source .venv/bin/activate
- pip install -r requirements.txt
- uvicorn app.main:app --reload --port 8004

### Frontend
- cd exercise_8/frontend
- npm install
- npm run dev -- --port 3004

## Main endpoints
- POST /api/run → { run_id, trace_id }
- GET /api/blackboard/{run_id}
- POST /api/hitl/risk-approve
- POST /api/hitl/final-approve
- POST /api/export/redline
- GET /api/report/slos
- GET /api/replay/{run_id}

## Notes
- Blackboard is in-memory for class; replace with DB if desired.
- Policies and contracts are safe classroom samples.
