# Deployment Runbook

Quick reference for handling common deployment issues and procedures.

## Quick Status Check

```bash
# Check CI status
gh run list --workflow=ci.yml --limit 5

# Check CD status
gh run list --workflow=cd.yml --limit 5

# Check service health
curl http://staging.example.com:8011/healthz
curl http://staging.example.com:8011/readyz
```

---

## Failed CI Pipeline

### Symptoms
- ❌ Red badge on GitHub
- Merge blocked
- PR shows failing checks

### Diagnosis

1. **Check failing job**:
   ```bash
   gh run view <run-id>
   ```

2. **Common failures**:
   - **Lint Backend**: Code style issues
     ```bash
     cd backend
     black app/ tests/
     flake8 app/
     ```
   
   - **Type Check**: Type errors
     ```bash
     mypy app/
     ```
   
   - **Unit Tests**: Test failures
     ```bash
     pytest tests/ -v
     ```
   
   - **Lint Frontend**: TypeScript errors
     ```bash
     cd frontend
     npx tsc --noEmit
     ```
   
   - **E2E Tests**: Playwright failures
     ```bash
     cd frontend
     npx playwright test e2e/assistant.spec.ts
     ```

### Resolution

1. Fix issues locally
2. Commit and push fix
3. CI will re-run automatically
4. Merge when green ✅

---

## Failed CD Pipeline

### Symptoms
- ❌ Deployment job failed
- Services not updating
- Health checks failing

### Diagnosis

1. **Check deployment logs**:
   ```bash
   gh run view <run-id> --log | grep -i error
   ```

2. **Verify images built successfully**:
   ```bash
   docker images | grep exercise11
   ```

3. **Check registry**:
   ```bash
   gh auth login
   gh api user/packages/container
   ```

### Resolution

1. **If build failed**:
   - Check Dockerfile syntax
   - Verify dependencies
   - Test build locally: `docker build -f backend/Dockerfile .`

2. **If push failed**:
   - Verify GitHub token has package write permissions
   - Check registry access

3. **If deployment failed**:
   - Verify environment variables
   - Check service configuration
   - Review deployment logs

4. **Rollback if needed**:
   ```bash
   # Use previous version
   docker pull ghcr.io/<repo>/backend:v0.9.0
   docker tag ghcr.io/<repo>/backend:v0.9.0 ghcr.io/<repo>/backend:latest
   docker push ghcr.io/<repo>/backend:latest
   ```

---

## Service Health Issues

### Backend Unhealthy

**Symptoms**: `/healthz` or `/readyz` returns error

**Check**:
```bash
# Check if service is running
docker ps | grep backend

# Check logs
docker compose logs backend

# Test locally
curl http://localhost:8011/healthz
```

**Common Issues**:
- Missing `OPENAI_API_KEY` → Add to `.env`
- Port 8011 already in use → Change port or stop conflicting service
- Python import errors → Check `sys.path` in `main.py`

**Fix**:
```bash
# Restart service
docker compose restart backend

# Or rebuild
docker compose up -d --build backend
```

---

### Frontend Unhealthy

**Symptoms**: Frontend not loading or API errors

**Check**:
```bash
# Check if service is running
docker ps | grep frontend

# Check logs
docker compose logs frontend

# Test API connection
curl http://localhost:3082
```

**Common Issues**:
- Backend not reachable → Check `NEXT_PUBLIC_API_URL`
- Build errors → Check `npm run build`
- Port 3082 in use → Change port

**Fix**:
```bash
# Restart service
docker compose restart frontend

# Or rebuild
docker compose up -d --build frontend
```

---

## Emergency Rollback

**When**: Production issue, service down, critical bug

**Steps**:

1. **Stop current deployment**:
   ```bash
   docker compose down
   ```

2. **Pull previous stable version**:
   ```bash
   docker pull ghcr.io/<repo>/backend:v<previous>
   docker pull ghcr.io/<repo>/frontend:v<previous>
   ```

3. **Tag as latest**:
   ```bash
   docker tag ghcr.io/<repo>/backend:v<previous> ghcr.io/<repo>/backend:latest
   docker tag ghcr.io/<repo>/frontend:v<previous> ghcr.io/<repo>/frontend:latest
   ```

4. **Deploy previous version**:
   ```bash
   docker compose up -d
   ```

5. **Verify**:
   ```bash
   curl http://localhost:8011/healthz
   curl http://localhost:3082
   ```

6. **Notify team**: Document issue and rollback reason

---

## Manual Deployment

**When**: CD pipeline not available, local deployment needed

**Steps**:

1. **Build images**:
   ```bash
   docker build -f backend/Dockerfile -t exercise11-backend:local .
   docker build -f frontend/Dockerfile.web -t exercise11-frontend:local .
   ```

2. **Tag for registry** (if pushing):
   ```bash
   docker tag exercise11-backend:local ghcr.io/<repo>/backend:local
   docker push ghcr.io/<repo>/backend:local
   ```

3. **Deploy**:
   ```bash
   docker compose up -d
   ```

4. **Verify**:
   ```bash
   docker compose ps
   curl http://localhost:8011/healthz
   curl http://localhost:3082
   ```

---

## Dependency Updates

**When**: Dependabot creates PR or manual update needed

**Check Dependabot PRs**:
```bash
gh pr list --label "dependencies"
```

**Review PR**:
- Check changelog for breaking changes
- Verify tests still pass
- Merge if safe

**Manual Update**:
```bash
# Backend
cd backend
pip install --upgrade <package>
pip freeze > requirements.txt

# Frontend
cd frontend
npm install <package>@latest
npm update
```

---

## Monitoring

### CI Metrics
- Build time: Should be <10 minutes
- Test coverage: Track with `pytest --cov`
- Success rate: Monitor via GitHub Actions

### CD Metrics
- Deployment time: Should be <5 minutes
- Success rate: Monitor deployments
- Rollback frequency: Track issues

### Service Metrics
- Health check response time: Should be <100ms
- Uptime: Monitor with health checks
- Error rate: Check logs for errors

---

## Contacts

- **CI/CD Issues**: Check GitHub Actions logs
- **Infrastructure**: Contact DevOps team
- **Security**: Report to security team
- **Emergency**: Use escalation procedure

---

*Last Updated: 2025-11-03*

