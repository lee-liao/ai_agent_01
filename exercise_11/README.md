# Exercise 11: Child Growth Assistant (Week 8)

[![CI](https://github.com/lee-liao/mygitactions/actions/workflows/superlinter.yml/badge.svg)](https://github.com/lee-liao/mygitactions/actions/workflows/superlinter.yml)
[![CD](https://github.com/lee-liao/mygitactions/actions/workflows/superlinter.yml/badge.svg)](https://github.com/lee-liao/mygitactions/actions/workflows/superlinter.yml)

> **Note**: Replace `YOUR_USERNAME/YOUR_REPO` with your actual GitHub repository path to enable badges.

This exercise bootstraps a Child Growth/Parenting Coach assistant as an evolution of Exercise 10. It includes:

- **Backend (FastAPI)**: Health endpoints, coach WebSocket chat for parenting advice
- **Frontend (Next.js)**: Beautiful, production-quality UI with parent sign-in and real-time chat

## 🚀 Quick Start

**Easiest way to get started:**

```bash
# Mac/Linux
./start.sh

# Windows
start.bat
```

This will automatically start both servers and open the app at http://localhost:3082

**For detailed instructions, troubleshooting, and manual setup**, see [QUICKSTART.md](./QUICKSTART.md)

## 🌐 URLs

Once running:
- **Frontend App**: http://localhost:3082
- **Backend API**: http://localhost:8011
- **API Docs**: http://localhost:8011/docs
- **Health Check**: http://localhost:8011/healthz

## 🏗️ Architecture

### Backend (Port 8011)
- FastAPI with WebSocket support
- Health endpoints: `/healthz` and `/readyz`
- Coach WebSocket: `ws://localhost:8011/ws/coach/{session_id}`
- Auto-reload enabled for development

### Frontend (Port 3082)
- Next.js 14 with App Router
- Tailwind CSS with custom animations
- Real-time WebSocket chat
- Responsive, accessible design

## Student Tasks (Week 8)

Complete the following to harden the MVP and prepare an internal alpha launch. Each item has a concrete deliverable and pass/fail criteria.

1) Safety & scope policy
- Deliverables: `docs/safety_scope.md`, `config/safety_policy.json`, backend guard hook with refusal templates.
- Pass: 20 red-team prompts trigger correct refusal/redirect (unit tests).

2) Refusal templates UI
- Deliverables: Supportive copy + resource links (hotlines, referrals); render with empathy in UI via `RefusalMessage` component.
- Pass: All refusals show empathy statement + clickable resource link.

3) Curated RAG pack (citations required)
- Deliverables: `rag/ingest.py`, `rag/index.json`, retrieval helper, citation badges/links in UI.
- Pass: In 10 sampled sessions, ≥90% responses include ≥1 citation.

4) SSE advice streaming
- Deliverables: backend SSE endpoint that streams advice chunks; frontend consumer in `/coach/chat`.
- Pass: First token <1.5s; streaming updates visible.

5) Playwright e2e suite
- Deliverables: expand `frontend/e2e/assistant.spec.ts` to ≥10 scenarios (screen time, bedtime, sibling conflict, motivation, ADHD-like guidance → safe referral, etc.).
- Pass: All scenarios green; asserts response structure (empathy, 3 steps, citation, safety footer).

6) Dockerize & health checks
- Deliverables: `Dockerfile`(API), `Dockerfile.web`(Next), `docker-compose.yml`, `/readyz` checks RAG + model key.
- Pass: `docker compose up` → both services healthy ≤20s.

7) CI/CD pipelines
- Deliverables: `.github/workflows/ci.yml` (lint/type, unit, e2e, build), `.github/workflows/cd.yml` (staging smoke deploy).
- Pass: Red blocks merge; green tag auto-deploys to staging.

8) SLOs & observability
- Deliverables: `observability/` with OpenTelemetry spans (retrieval, model, guard), dashboards (JSON exports).
- Pass: 15‑min load test p95 ≤ 2.5s; failure rate ≤ 1%.

9) Guardrails + HITL queue
- Deliverables: `backend/app/guardrails.py` (PII/crisis/medical classifier) ↔ HITL UI `web/app/(hitl)/queue.tsx`.
- Pass: Crisis prompts route to HITL in <500ms; mentor reply appears in parent chat.

10) Prompt versioning & snapshots
- Deliverables: `prompts/child_coach_vX.json`, `tests/snapshots/*`, prompt changelog.
- Pass: Changing prompts without version bump fails CI.

11) Token/cost watchdog
- Deliverables: `billing/ledger.py` (per‑turn tokens/cost), caps + "lite mode" fallback, nightly CSV + admin sparkline.
- Pass: Over‑budget requests return lite mode with notice; report generated daily.

12) Load testing
- Deliverables: Use scaffolds in `load/k6/coach_scenario.js` and `load/locust/locustfile.py`.
- Pass: Report includes throughput, p95, error rate; meets SLOs.

13) Accessibility & UX polish
- Deliverables: keyboard navigation, ARIA roles for chat, disclaimers.
- Pass: Axe scan has no critical issues.

14) Alpha test protocol
- Deliverables: `docs/alpha_plan.md`, consent copy, feedback form, 10 issues logged.
- Pass: ≥80% "felt-helpful", 0 P0 safety bugs.

15) Demo & one-pager
- Deliverables: 2-minute demo video (refusal → normal advice w/ citations → HITL); one-pager report (p95, fail rate, citation rate, cost/day, risks, next steps).
- Pass: Demo reproducible from `docker compose up`; metrics align with SLOs.

## What to Submit

- **3–5 merged PRs** covering: Safety+RAG+Refusal UI, Docker+CI, E2E+SLOs+Observability.
- **Alpha test results** (Task 14): Feedback summary, helpfulness ≥80%, 0 P0 safety bugs.
- **Demo & one-pager** (Task 15): 2-minute video showing refusal → normal advice with citations → HITL escalation; plus one-page report with metrics, costs, risks, and next steps.

## 📖 Documentation Index

### Getting Started
- **[WELCOME.md](./WELCOME.md)** - 👋 Start here! Introduction and overview
- **[QUICKSTART.md](./QUICKSTART.md)** - 🚀 Setup guide and troubleshooting
- **[SCRIPTS.md](./SCRIPTS.md)** - 🛠️ Scripts reference and commands
- **[PROJECT_STRUCTURE.md](./PROJECT_STRUCTURE.md)** - 📁 Codebase layout and architecture

### CI/CD & Deployment
- **[docs/deployment.md](./docs/deployment.md)** - 📦 Complete CI/CD pipeline and deployment guide
- **[docs/runbook.md](./docs/runbook.md)** - 🆘 Troubleshooting runbook for deployment issues
- **[.github/CONTRIBUTING.md](./.github/CONTRIBUTING.md)** - 🤝 Contributing guide with PR workflow

### Testing & Development
- **[load/README.md](./load/README.md)** - 🧪 Load testing guide (K6 & Locust)
- **[docs/SAFETY_SCOPE_IMPLEMENTATION_CHECK.md](./docs/SAFETY_SCOPE_IMPLEMENTATION_CHECK.md)** - 🛡️ Safety implementation guide

### Project Management
- **[OPENSPEC_SETUP_COMPLETE.md](./OPENSPEC_SETUP_COMPLETE.md)** - 📋 OpenSpec proposals for all 15 tasks
- **[CLASS_NOTES_INTEGRATED.md](./CLASS_NOTES_INTEGRATED.md)** - 📝 Integration of class notes into OpenSpec

## Tips

- **Use OpenSpec workflow**: Each task has a detailed proposal in `openspec/changes/`. Run `openspec list` to see all tasks, `openspec show <task-name>` for details.
- Keep `.env` and secrets out of source control; use templates.
- Add feature flags for streaming vs non‑streaming and model choices.
- Prefer small, reviewable PRs; ensure CI is green before merging.
- Follow the recommended implementation order in `OPENSPEC_SETUP_COMPLETE.md` for best results.
