# Add Docker & Health Checks

## Why
Containerization enables consistent deployment across environments. Robust health checks ensure services are truly ready before accepting traffic, preventing failed requests during startup.

## What Changes
- Create `Dockerfile` for backend API
- Create `Dockerfile.web` for Next.js frontend
- Create `docker-compose.yml` for local development
- Implement `/readyz` endpoint that checks RAG index and OpenAI API key
- Ensure `docker compose up` brings both services healthy ≤20s

## Impact
- Affected specs: New capability `docker-deployment`
- Affected code:
  - `Dockerfile` - Backend container
  - `Dockerfile.web` - Frontend container
  - `docker-compose.yml` - Orchestration
  - `backend/app/api/health.py` - Enhanced health checks
  - `.dockerignore` - Exclude unnecessary files

