# Deployment Guide

This document describes the CI/CD pipeline and deployment process for the Child Growth Assistant.

## How to Use CI/CD

### Trigger CI

CI runs automatically on every push and pull request. To manually trigger CI:

```bash
# Create a feature branch
git checkout -b feature/my-feature

# Make your changes and commit
git add .
git commit -m "feat: add new feature"

# Push to trigger CI
git push origin feature/my-feature

# Create PR on GitHub - CI will run automatically
# Or use GitHub CLI:
gh pr create --title "feat: add new feature" --body "Description"
```

**View CI status**:
```bash
# View CI workflow (note: workflow is at repository root)
gh workflow view exercise_11_ci.yml

# List recent CI runs
gh run list --workflow=exercise_11_ci.yml

# View specific run
gh run view <run-id>
```

### Trigger CD

CD deploys to staging when you push a version tag:

```bash
# Tag a version to deploy
git tag v1.0.0
git push origin v1.0.0

# CD pipeline will automatically:
# - Build Docker images
# - Push to registry
# - Deploy to staging
# - Run smoke tests
```

**View CD status**:
```bash
# View CD workflow (note: workflow is at repository root)
gh workflow view exercise_11_cd.yml

# List recent deployments
gh run list --workflow=exercise_11_cd.yml

# View deployment logs
gh run view <run-id> --log
```

**Tag format**: `v*.*.*` (e.g., `v1.0.0`, `v1.2.3`, `v2.0.0-beta.1`)

---

## CI Pipeline

The Continuous Integration (CI) pipeline runs on every push and pull request to `main` and `develop` branches. It includes:

### Jobs

1. **Lint Backend (Python)**
   - Runs `flake8` for code quality checks
   - Checks formatting with `black`
   - Fails on syntax errors; warnings for style issues

2. **Type Check Backend (Python)**
   - Runs `mypy` for type checking
   - Validates type annotations and catches type errors

3. **Unit Tests (Python)**
   - Runs `pytest` with all backend tests
   - Validates safety guardrails, cost tracking, and other backend logic
   - Requires 35 tests to pass

4. **Lint Frontend (TypeScript)**
   - Runs ESLint (if configured)
   - Type checks with `tsc --noEmit`
   - Validates TypeScript types

5. **E2E Tests (Playwright)**
   - Starts backend and frontend services
   - Runs Playwright end-to-end tests
   - Validates complete user flows

6. **Build Docker Images**
   - Builds backend and frontend Docker images
   - Validates Dockerfiles are correct
   - Only runs if all previous jobs pass

### Status

- ✅ **Green**: All checks passing, ready to merge
- ❌ **Red**: At least one check failed, merge blocked

### Branch Protection

The `main` branch is protected with:
- ✅ Require CI to pass before merging
- ✅ Require at least one code review approval
- ✅ Automatic branch deletion after merge

---

## CD Pipeline

The Continuous Deployment (CD) pipeline automatically deploys to staging when a version tag is pushed.

### Trigger

Deployment is triggered by pushing a version tag:
```bash
git tag v1.0.0
git push origin v1.0.0
```

Tag format: `v*.*.*` (e.g., `v1.0.0`, `v1.2.3`)

### Process

1. **Extract Version**: Parses version from tag name
2. **Build Docker Images**: Builds and tags backend/frontend images
3. **Push to Registry**: Pushes images to GitHub Container Registry (ghcr.io)
4. **Deploy to Staging**: Deploys new images to staging environment
5. **Smoke Tests**: Runs basic health checks after deployment
6. **Notify**: Sends deployment status notification

### Image Tags

Images are tagged with:
- Version-specific: `ghcr.io/<repo>/backend:v1.0.0`
- Latest: `ghcr.io/<repo>/backend:latest`

---

## Manual Deployment

### Prerequisites

- Docker and Docker Compose installed
- Access to container registry (if deploying remotely)
- Environment variables configured

### Local Deployment

```bash
cd exercise_11
docker compose up -d
```

### Staging Deployment

1. **Build Images**:
   ```bash
   docker build -f backend/Dockerfile -t exercise11-backend:latest .
   docker build -f frontend/Dockerfile.web -t exercise11-frontend:latest .
   ```

2. **Push to Registry**:
   ```bash
   docker tag exercise11-backend:latest ghcr.io/<repo>/backend:latest
   docker push ghcr.io/<repo>/backend:latest
   ```

3. **Deploy**:
   - Update your orchestration (Kubernetes, Docker Swarm, etc.)
   - Or use `docker compose` on the server

---

## Environment Variables

### Backend

Required in `backend/.env`:
- `OPENAI_API_KEY`: OpenAI API key for LLM
- `CORS_ORIGINS`: Allowed CORS origins (comma-separated)

### Frontend

Required environment variables:
- `NEXT_PUBLIC_API_URL`: Backend API URL (default: `http://localhost:8011`)

---

## Health Checks

After deployment, verify services are healthy:

```bash
# Backend health
curl http://staging.example.com:8011/healthz
# Expected: {"status":"ok"}

# Backend readiness
curl http://staging.example.com:8011/readyz
# Expected: {"ready":true,"checks":{...}}

# Frontend
curl http://staging.example.com:3082
# Expected: HTML response
```

---

## Rollback Procedure

If deployment fails:

1. **Identify Issue**: Check deployment logs and health endpoints
2. **Rollback Images**: Revert to previous version tag
   ```bash
   docker pull ghcr.io/<repo>/backend:v0.9.0
   docker tag ghcr.io/<repo>/backend:v0.9.0 ghcr.io/<repo>/backend:latest
   ```
3. **Redeploy**: Restart services with previous images
4. **Verify**: Run smoke tests to confirm rollback successful
5. **Document**: Log issue and resolution

---

## Troubleshooting

### CI Fails

**Common Issues**:
- Linter errors: Run `black` and `flake8` locally to fix
- Test failures: Run `pytest tests/ -v` to debug
- Type errors: Run `mypy app/` to identify issues

**Fix Locally**:
```bash
cd backend
black app/ tests/
flake8 app/
mypy app/
pytest tests/ -v
```

### CD Fails

**Common Issues**:
- Docker build fails: Check Dockerfiles for errors
- Registry push fails: Verify authentication
- Deployment fails: Check environment variables and service configs

**Verify Images**:
```bash
docker images | grep exercise11
docker run --rm exercise11-backend:latest curl http://localhost:8011/healthz
```

### Services Unhealthy

**Check Logs**:
```bash
docker compose logs backend
docker compose logs frontend
```

**Common Causes**:
- Missing environment variables
- Port conflicts
- Database/API connectivity issues

---

## Dependabot

Dependencies are automatically updated via Dependabot:

- **Python**: Weekly updates for `backend/requirements.txt`
- **Node.js**: Weekly updates for `frontend/package.json`
- **Docker**: Weekly updates for Docker base images

Dependabot creates PRs with dependency updates. Review and merge to keep dependencies current.

---

## Security

- Secrets stored in GitHub Actions secrets (never in code)
- Docker images scanned for vulnerabilities
- Dependencies monitored for security advisories
- Automatic security updates via Dependabot

---

*Last Updated: 2025-11-03*

