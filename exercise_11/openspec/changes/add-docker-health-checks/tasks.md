# Implementation Tasks

## 1. Backend Dockerfile
- [ ] 1.1 Create `Dockerfile` with Python 3.11 base
- [ ] 1.2 Install dependencies from `requirements.txt`
- [ ] 1.3 Copy application code
- [ ] 1.4 Expose port 8011
- [ ] 1.5 Set CMD to run uvicorn

## 2. Frontend Dockerfile
- [ ] 2.1 Create `Dockerfile.web` with Node 18
- [ ] 2.2 Install dependencies from `package.json`
- [ ] 2.3 Build Next.js application
- [ ] 2.4 Expose port 3082
- [ ] 2.5 Set CMD to run Next.js server

## 3. Docker Compose
- [ ] 3.1 Create `docker-compose.yml`
- [ ] 3.2 Define backend service with health check
- [ ] 3.3 Define frontend service with health check
- [ ] 3.4 Configure environment variables
- [ ] 3.5 Set up networking and volumes

## 4. Readiness Endpoint
- [ ] 4.1 Implement `/readyz` endpoint
- [ ] 4.2 Check RAG index file exists
- [ ] 4.3 Verify OpenAI API key is set
- [ ] 4.4 Return 503 if not ready, 200 if ready
- [ ] 4.5 Add detailed status information

## 5. Testing & Optimization
- [ ] 5.1 Test `docker compose up` from clean state
- [ ] 5.2 Measure startup time to healthy status
- [ ] 5.3 Assert ≤20 seconds
- [ ] 5.4 Optimize image size with multi-stage builds
- [ ] 5.5 Create `.dockerignore` files

