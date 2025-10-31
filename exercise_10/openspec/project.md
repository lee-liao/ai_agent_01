# Project Context

## Purpose
Build a real-time AI call center assistance platform where an AI agent supports human call center agents during live calls. The system captures audio, performs real-time transcription, surfaces customer context from the database, and streams actionable AI suggestions to improve resolution speed, compliance, and customer satisfaction.

## Tech Stack
- Backend: Python 3.11, FastAPI, Uvicorn, SQLAlchemy (async), Pydantic v2, websockets, python-jose, passlib, redis client, python-dotenv
- Database: PostgreSQL via Docker (dev/prod), fallback SQLite (aiosqlite) for local dev
- Frontend: Next.js 14 (App Router), React 18, TypeScript, TailwindCSS, Framer Motion
- Streaming: WebSocket for audio + control messages; optional SSE/HTTP streaming patterns
- AI/ML: OpenAI SDK (LLM + Whisper STT planned), room for Deepgram/others
- Containers/Infra: Docker, docker-compose, Redis (session/state), env configuration

## Project Conventions

### Code Style
- Backend (Python):
  - Async-first APIs and DB access (async def, AsyncSession)
  - Pydantic models use Config.from_attributes = True
  - Use snake_case for variables/functions; PascalCase for Pydantic schemas and SQLAlchemy models
  - Keep routers modular under backend/app/api/* with APIRouter(prefix=...)
  - Environment-driven settings via pydantic-settings (backend/app/config.py) and .env
  - Prefer explicit imports and typed signatures; avoid one-letter names
- Frontend (TypeScript/React):
  - Strict TS (tsconfig.json has strict: true), path alias @/* to src/*
  - Next.js App Router under frontend/src/app/* with server/client components as needed
  - Use functional components and hooks; colocate lib helpers under frontend/src/lib/*
  - Tailwind for styling; shared theme tokens in tailwind.config.js
  - Naming: camelCase for variables/functions; PascalCase for components; kebab-case for filenames

### Architecture Patterns
- Layered API: FastAPI app with lifespan hooks for DB init/close
- Feature routers: auth, customers, calls, websocket kept independent and included in app.main
- Data layer: SQLAlchemy models in backend/app/models.py; async sessions via backend/app/database.py
- Real-time channel: WebSocket endpoint /ws/call/{call_id} manages active connections and routes audio/transcript between paired participants
- Frontend app: Next.js App Router pages under src/app, using rewrites to proxy /api/* to backend (next.config.js)
- Config separation: Runtime via env vars; Docker compose wires services for local dev

### Testing Strategy
- Unit tests (planned):
  - Backend: routers, auth utilities, DB models (with SQLite test DB)
  - Frontend: component behavior and hooks (Jest/React Testing Library)
- Integration tests (planned):
  - WebSocket call flow: connect, send audio/text, receive events
  - Auth flow: register, login, token validation, protected routes
- Manual testing:
  - customer-sim/ for basic WebSocket audio/control testing
  - Seed data scripts under data/ for customer/order/ticket records

### Git Workflow
- Branching: main with feature branches feature/<name> and fix/<name>
- Commits: Conventional Commit style (feat:, fix:, docs:, chore:, refactor:, test:)
- Pull requests: Require succinct description, related tasks/spec links, and checklist
- OpenSpec changes: Use openspec/changes/<change-id> with verb-led kebab-case (add-, update-, remove-, refactor-)

## Domain Context
- Call center setting with human agents supported by AI.
- Entities: User (agent/admin), Customer, Call, Transcript, AISuggestion, Order, Ticket.
- Typical flow: agent starts/joins a call; system captures audio; transcription/AI suggestions stream to UI; customer context (orders/tickets/LTV) is fetched to assist resolution.
- Roles: agent, supervisor, admin control access; auth via OAuth2 password flow + JWT.

## Important Constraints
- Privacy: Do not persist raw audio without explicit consent; recordings optional and must be protected.
- Security: JWT secrets and API keys must be set via environment; never hardcode.
- Performance: Real-time UI updates should target sub-second latency; avoid blocking calls in WebSocket handlers.
- Reliability: Handle WebSocket disconnects gracefully; clean up active_connections.
- Compliance: Be mindful of call recording/transcription laws per region.

## External Dependencies
- PostgreSQL (Docker service postgres) – primary relational DB
- Redis (Docker service redis) – ephemeral state/session/pub-sub (future)
- OpenAI API – LLM and Whisper STT integration (via openai SDK)
- Browser Web APIs – WebRTC, MediaDevices, WebSocket
- Docker – local orchestration for backend/frontend/DB/cache

## Local Dev Setup
- Prereqs: Docker/Docker Compose, Node 18+, Python 3.11, OpenAI API key.
- Start services: `docker-compose up --build`
- Backend API: `http://localhost:8000` (FastAPI), health at `/health`, docs at `/docs`.
- Frontend UI: `http://localhost:3000` (Next.js dev server).
- Database: `postgres` service (`callcenter` DB, `admin/password`).
- Cache: `redis` service for future state/pub-sub.
- Seed data: run `data/seed_data.py` (uses SQLite by default) or adapt for Postgres.

## Ports and Env Vars
- Ports:
  - `8000`: Backend API (Uvicorn)
  - `3000`: Frontend (Next.js dev)
  - `5432`: PostgreSQL
  - `6379`: Redis
- Key env vars:
  - Backend: `DATABASE_URL`, `REDIS_URL`, `OPENAI_API_KEY`, `SECRET_KEY`, `CORS_ORIGINS`
  - Frontend: `NEXT_PUBLIC_API_URL`, `NEXT_PUBLIC_WS_URL`, `NEXTAUTH_SECRET`, `NEXTAUTH_URL`
  - Suggested `.env` files: `backend/.env`, `frontend/.env.local`

## Testing Utilities
- `customer-sim/` (HTML simulator):
  - Purpose: lightweight debug utility to test WebSocket pairing, routing, and transcript flow without the full Next.js app.
  - Use when: quickly reproducing backend issues, verifying call start/end flow, or testing message handling.
  - Not production: no auth/roles, no real audio capture; intended for local/manual checks.
  - How to run: open `customer-sim/index.html` directly or serve with `python -m http.server 8080` and visit `http://localhost:8080`.
- Main frontend (`frontend/`):
  - Purpose: agent UI with Next.js, auth screens, and integration points for audio, transcripts, AI suggestions, and customer context.
  - Use when: validating end-to-end UX, auth, and real-time features in the app environment.
