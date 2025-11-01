# Project Context

## Purpose
Build a production-ready AI-powered Child Growth/Parenting Coach assistant that provides evidence-based parenting advice through real-time chat. The system helps parents with child development questions while maintaining safety boundaries, providing cited information from trusted sources, and escalating sensitive cases to human mentors when needed.

## Tech Stack
- **Backend**: Python 3.11, FastAPI, Uvicorn (async), WebSocket, OpenAI SDK (LLM + optional Whisper STT)
- **Frontend**: Next.js 14 (App Router), React 18, TypeScript, Tailwind CSS, WebSocket client
- **AI/RAG**: OpenAI GPT models, vector embeddings, retrieval-augmented generation, prompt versioning
- **Testing**: Playwright (e2e), pytest (unit), K6 & Locust (load testing)
- **Observability**: OpenTelemetry spans, metrics dashboards, SLO tracking
- **Infrastructure**: Docker, docker-compose, health checks (`/healthz`, `/readyz`)
- **CI/CD**: GitHub Actions (lint, test, build, deploy)

## Project Conventions

### Code Style
- **Backend (Python)**:
  - Async-first with `async def` functions
  - Snake_case for variables/functions; PascalCase for classes
  - Type hints required for all function signatures
  - Pydantic models for request/response validation
  - Keep routers modular under `backend/app/api/*`
  - Configuration via environment variables (`backend/app/config.py`)
- **Frontend (TypeScript/React)**:
  - Strict TypeScript (`tsconfig.json` has `strict: true`)
  - Path alias `@/*` maps to `src/*`
  - Functional components with hooks
  - CamelCase for variables/functions; PascalCase for components
  - Kebab-case for filenames
  - Tailwind CSS for styling

### Architecture Patterns
- **Layered API**: FastAPI app with health endpoints, coach REST API, and WebSocket endpoints
- **Real-time Communication**: WebSocket at `/ws/coach/{session_id}` for bidirectional messaging
- **RAG Pipeline**: Document ingestion → vector index → retrieval → LLM with citations
- **Safety Layer**: Guardrails check every request for PII/crisis/medical concerns before processing
- **HITL Queue**: Sensitive cases route to human mentors; responses return to parent chat
- **Feature Flags**: Toggle streaming vs non-streaming, model selection, RAG enabled/disabled
- **Cost Control**: Token tracking per request, budget caps, fallback to "lite mode"

### Testing Strategy
- **Unit Tests**:
  - Backend: Test routers, guardrails, RAG retrieval, prompt versioning
  - Frontend: Test components, hooks, API clients
- **E2E Tests** (Playwright):
  - Cover 10+ scenarios: normal advice, refusal flow, HITL escalation, citations display
  - Assert response structure (empathy, steps, citations, safety footer)
- **Load Tests** (K6 & Locust):
  - Validate p95 latency ≤ 2.5s, failure rate ≤ 1%
  - Simulate concurrent users and WebSocket connections
- **Snapshot Tests**:
  - Prompt versioning: changing prompts without version bump fails CI

### Git Workflow
- **Branching**: `main` with feature branches `feature/<name>` and `fix/<name>`
- **Commits**: Conventional Commits (`feat:`, `fix:`, `docs:`, `chore:`, `refactor:`, `test:`)
- **Pull Requests**: Require description, spec links, checklist, passing CI
- **OpenSpec Changes**: Use `openspec/changes/<change-id>` with verb-led kebab-case IDs

## Domain Context
- **Users**: Parents seeking guidance on child development, behavior, routines, emotional support
- **Age Ranges**: Typically 0-12 years old (infants, toddlers, school-age)
- **Topics**: Sleep routines, nutrition, discipline, social skills, developmental milestones, screen time, sibling rivalry, school readiness, ADHD-like concerns
- **Safety Boundaries**: 
  - **In-scope**: General parenting advice, developmental guidance, behavior strategies
  - **Out-of-scope**: Medical diagnosis, crisis intervention, legal advice, therapy
- **Escalation**: Crisis/medical/PII detected → route to HITL queue
- **Citations Required**: All advice must reference vetted sources (AAP, CDC, peer-reviewed research)

## Important Constraints
- **Safety First**: Never provide medical diagnosis or crisis counseling; must redirect to professionals
- **Privacy**: Do not log or persist PII; conversations ephemeral unless explicitly saved
- **Accuracy**: All advice must be grounded in RAG sources with citations displayed
- **Performance**: Target p95 latency ≤ 2.5s, first token < 1.5s for streaming
- **Reliability**: System failure rate must be ≤ 1%
- **Cost Control**: Daily budget cap; fallback to lite mode when exceeded
- **Accessibility**: WCAG AA compliance; keyboard navigation; screen reader support
- **Compliance**: Data residency, age-appropriate content, transparent AI disclosure

## External Dependencies
- **OpenAI API**: GPT-4 or GPT-3.5-turbo for LLM, embeddings for RAG
- **RAG Sources**: Curated content from AAP (American Academy of Pediatrics), CDC, peer-reviewed journals
- **Monitoring**: OpenTelemetry for traces/metrics, dashboard tools (Grafana/Datadog)
- **Browser APIs**: WebSocket for real-time chat

## Ports and Environment
- **Backend**: Port 8011 (`http://localhost:8011`)
- **Frontend**: Port 3082 (`http://localhost:3082`)
- **Key Env Vars**:
  - Backend: `OPENAI_API_KEY`, `RAG_INDEX_PATH`, `DAILY_BUDGET_USD`, `CORS_ORIGINS`
  - Frontend: `NEXT_PUBLIC_API_URL=http://localhost:8011`, `NEXT_PUBLIC_WS_URL=ws://localhost:8011`
