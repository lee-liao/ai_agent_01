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
git push origin feature/exercise-11-cicd-pipelines

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

## Configuration

### Setting Up GitHub Secrets

The CI/CD pipelines require secrets to be configured in your GitHub repository. Here's how to set them up:

#### 1. Navigate to Repository Settings

1. Go to your GitHub repository (e.g., `https://github.com/YOUR_USERNAME/YOUR_REPO`)
2. Click **Settings** (top menu bar)
3. In the left sidebar, click **Secrets and variables** → **Actions**

#### 2. Add OpenAI API Key

**Required for E2E tests to run with real API responses:**

1. Click **New repository secret**
2. **Name**: `OPENAI_API_KEY`
3. **Secret**: Paste your OpenAI API key (get it from https://platform.openai.com/api-keys)
4. Click **Add secret**

**Important Notes:**
- The secret name must match exactly: `OPENAI_API_KEY` (case-sensitive)
- The API key will be masked in logs (shown as `***`)
- You can use a test/CI-specific API key if you have usage limits
- Without this secret, E2E tests will gracefully skip content assertions (tests will still pass)

#### Other Environment Variables

**No other secrets are required!** The following environment variables from `backend/.env` are either:
- **Set directly in CI workflow** (hardcoded values)
- **Have safe defaults** (no secrets needed)

| Variable | CI/CD Handling | Notes |
|----------|---------------|-------|
| `OPENAI_API_KEY` | ✅ **Secret Required** | Added via GitHub Secrets |
| `CORS_ORIGINS` | ✅ Set in workflow | Hardcoded as `http://localhost:3082` in CI |
| `NEXT_PUBLIC_API_URL` | ✅ Set in workflow | Hardcoded as `http://localhost:8011` in CI |
| `NEXT_PUBLIC_WS_URL` | ✅ Set in workflow | Hardcoded as `ws://localhost:8011` in CI |
| `PORT` | ✅ Set in workflow | Hardcoded as `3082` in CI |

**Local Development**: Your `backend/.env` file is for local development only and is not used by CI/CD. The CI workflow sets all necessary environment variables directly.

#### 3. Verify Secret is Set

You can verify the secret exists by:
- Checking the workflow run logs - if the key is set, E2E tests will use real API calls
- Looking for API errors in test logs - if missing, you'll see "test-key-for-ci" fallback

#### 4. Using GitHub CLI (Alternative)

If you prefer using the command line:

```bash
# Set the secret (requires GitHub CLI and appropriate permissions)
gh secret set OPENAI_API_KEY --body "sk-your-api-key-here"
```

**Note**: Replace `sk-your-api-key-here` with your actual OpenAI API key.

#### 5. Environment-Specific Secrets (Advanced)

For different environments (staging, production), you can also set secrets at the environment level:

1. Go to **Settings** → **Environments**
2. Create or select an environment (e.g., `staging`)
3. Add secrets specific to that environment

This is useful if you want different API keys for different deployment stages.

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

