# Exercise 11: Child Growth Assistant (Week 8)

[![Exercise 11 CodeQL Security Analysis](https://github.com/lee-liao/ai_agent_01/actions/workflows/exercise_11_codeql.yml/badge.svg)](https://github.com/lee-liao/ai_agent_01/actions/workflows/exercise_11_codeql.yml)
[![Exercise 11 CI](https://github.com/lee-liao/ai_agent_01/actions/workflows/exercise_11_ci.yml/badge.svg)](https://github.com/lee-liao/ai_agent_01/actions/workflows/exercise_11_ci.yml)
[![Exercise 11 CD](https://github.com/lee-liao/ai_agent_01/actions/workflows/exercise_11_cd.yml/badge.svg)](https://github.com/lee-liao/ai_agent_01/actions/workflows/exercise_11_cd.yml)

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

### 🚀 Getting Started
- **[WELCOME.md](./WELCOME.md)** - 👋 Start here! Introduction and overview
- **[QUICKSTART.md](./QUICKSTART.md)** - 🚀 Setup guide and troubleshooting
- **[SCRIPTS.md](./SCRIPTS.md)** - 🛠️ Scripts reference and commands
- **[PROJECT_STRUCTURE.md](./PROJECT_STRUCTURE.md)** - 📁 Codebase layout and architecture

### 🔧 Setup & Configuration
- **[docs/OPENAI_SETUP.md](./docs/OPENAI_SETUP.md)** - 🔑 OpenAI API key configuration and setup
- **[docs/QUICK_API_SETUP.md](./docs/QUICK_API_SETUP.md)** - ⚡ Quick API setup guide
- **[docs/IMPLEMENTATION_GUIDE.md](./docs/IMPLEMENTATION_GUIDE.md)** - 📘 Step-by-step integration guide for frontend components

### 🧪 Testing Guides
- **[docs/MANUAL_TEST_GUIDE.md](./docs/MANUAL_TEST_GUIDE.md)** - 🧪 Manual testing procedures and test flows
- **[docs/SAFETY_SCOPE_IMPLEMENTATION_CHECK.md](./docs/SAFETY_SCOPE_IMPLEMENTATION_CHECK.md)** - 🛡️ Safety implementation validation guide
- **[load/README.md](./load/README.md)** - 🧪 Load testing guide (K6 & Locust scenarios)

### 🚢 CI/CD & Deployment
- **[docs/deployment.md](./docs/deployment.md)** - 📦 Complete CI/CD pipeline and deployment guide (includes "How to Use" section)
- **[docs/runbook.md](./docs/runbook.md)** - 🆘 Troubleshooting runbook for deployment issues and emergency procedures
- **[docs/CONTRIBUTING.md](./docs/CONTRIBUTING.md)** - 🤝 Contributing guide with PR workflow and code review process

### 🔒 Safety & Security
- **[docs/safety_scope.md](./docs/safety_scope.md)** - 🛡️ Safety boundaries, scope limitations, and handling procedures
- **[docs/SAFETY_SCOPE_IMPLEMENTATION_CHECK.md](./docs/SAFETY_SCOPE_IMPLEMENTATION_CHECK.md)** - ✅ Safety implementation checklist and validation

### 📡 Technical Implementation
- **[docs/SSE_STREAMING_COMPLETE.md](./docs/SSE_STREAMING_COMPLETE.md)** - 📡 Server-Sent Events (SSE) streaming implementation details
- **[docs/DOCKER_COST_COMPLETE.md](./docs/DOCKER_COST_COMPLETE.md)** - 🐳 Docker deployment and cost tracking implementation summary
- **[docs/DOCKER_QUICK_TEST.md](./docs/DOCKER_QUICK_TEST.md)** - 🧪 Quick Docker testing procedures

### 📊 Project Status & Planning
- **[docs/DEMO_READY.md](./docs/DEMO_READY.md)** - 🎯 Complete implementation & demo guide (single source of truth)
- **[docs/TASKS_1-5_COMPLETE.md](./docs/TASKS_1-5_COMPLETE.md)** - ✅ Summary of tasks 1-5 implementation
- **[docs/NEXT_4_HOURS_PLAN.md](./docs/NEXT_4_HOURS_PLAN.md)** - ⏱️ Implementation plan for next 4 hours (Option A: Docker + Cost, Option B: Polish)
- **[docs/IMPLEMENTATION_COMPLETE.md](./docs/IMPLEMENTATION_COMPLETE.md)** - ✅ Overall implementation completion summary
- **[docs/IMPLEMENTATION_STATUS.md](./docs/IMPLEMENTATION_STATUS.md)** - 📈 Detailed OpenSpec task tracking and status
- **[docs/READY_FOR_DEMO.md](./docs/READY_FOR_DEMO.md)** - 🎬 Demo readiness checklist and preparation guide

### 📋 OpenSpec & Project Management
- **[docs/OPENSPEC_SETUP_COMPLETE.md](./docs/OPENSPEC_SETUP_COMPLETE.md)** - 📋 OpenSpec proposals for all 15 tasks
- **[docs/CLASS_NOTES_INTEGRATED.md](./docs/CLASS_NOTES_INTEGRATED.md)** - 📝 Integration of class notes into OpenSpec
- **[docs/QUICK_DEMO_PLAN.md](./docs/QUICK_DEMO_PLAN.md)** - 🎯 Quick demo implementation plan
- **[docs/AGENTS.md](./docs/AGENTS.md)** - 🤖 AI agent instructions for OpenSpec workflow
- **[openspec/AGENTS.md](./openspec/AGENTS.md)** - 🤖 OpenSpec agent instructions (canonical source)

### 📚 Additional Resources
- **[rag/sources/README.md](./rag/sources/README.md)** - 📚 RAG source documentation

## Tips

- **Use OpenSpec workflow**: Each task has a detailed proposal in `openspec/changes/`. Run `openspec list` to see all tasks, `openspec show <task-name>` for details.
- Keep `.env` and secrets out of source control; use templates.
- Add feature flags for streaming vs non‑streaming and model choices.
- Prefer small, reviewable PRs; ensure CI is green before merging.
- Follow the recommended implementation order in `OPENSPEC_SETUP_COMPLETE.md` for best results.

# CI trigger for branch protection

# Test PR for status checks visibility

# Testing branch protection - status checks required
