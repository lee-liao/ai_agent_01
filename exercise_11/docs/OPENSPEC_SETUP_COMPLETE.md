# OpenSpec Setup Complete ✅

## Summary

Successfully set up OpenSpec workflow for Exercise 11 (Child Growth Assistant) with comprehensive project documentation and **15 change proposals** for Week 8 assignments (including 3 additional items from class notes).

---

## What Was Created

### 1. Project Documentation
**File**: `openspec/project.md`

Filled out with comprehensive details:
- Project purpose and goals
- Complete tech stack (FastAPI, Next.js, OpenAI, Docker, etc.)
- Code style conventions for Python and TypeScript
- Architecture patterns (RAG, HITL, safety guardrails)
- Testing strategy (unit, e2e, load)
- Domain context (parenting advice, age ranges, safety boundaries)
- Important constraints (safety, privacy, performance SLOs)

### 2. OpenSpec Change Proposals (15 Total)

All proposals include:
- ✅ `proposal.md` - Why, what changes, impact
- ✅ `tasks.md` - Detailed implementation checklist
- ✅ `specs/<capability>/spec.md` - Requirements with scenarios
- ✅ **All passed validation** with `openspec validate --strict`

---

## The 15 Change Proposals

| # | Change ID | Capability | Tasks | Status | Notes |
|---|-----------|------------|-------|--------|-------|
| 1 | `add-safety-scope-policy` | safety-guardrails | 16 | ✅ Valid | Red-team testing |
| 2 | `add-refusal-templates-ui` | safety-guardrails | 28 | ✅ Valid | **NEW from class notes** |
| 3 | `add-curated-rag-pack` | rag-retrieval | 25 | ✅ Valid | Citations required |
| 4 | `add-sse-advice-streaming` | sse-streaming | 22 | ✅ Valid | <1.5s first token |
| 5 | `add-playwright-e2e-suite` | e2e-testing | 23 | ✅ Valid | 10+ scenarios |
| 6 | `add-docker-health-checks` | docker-deployment | 25 | ✅ Valid | ≤20s startup |
| 7 | `add-cicd-pipelines` | cicd-automation | 25 | ✅ Valid | GitHub Actions |
| 8 | `add-slos-observability` | observability | 25 | ✅ Valid | OpenTelemetry |
| 9 | `add-guardrails-hitl-queue` | hitl-queue | 26 | ✅ Valid | <500ms routing |
| 10 | `add-prompt-versioning-snapshots` | prompt-versioning | 25 | ✅ Valid | CI enforcement |
| 11 | `add-token-cost-watchdog` | cost-management | 25 | ✅ Valid | Budget caps |
| 12 | `add-load-testing` | load-testing | 30 | ✅ Valid | K6 & Locust |
| 13 | `add-accessibility-ux-polish` | accessibility | 36 | ✅ Valid | WCAG AA |
| 14 | `add-alpha-test-protocol` | alpha-testing | 46 | ✅ Valid | **NEW from class notes** |
| 15 | `add-demo-and-onepager` | demo-deliverables | 44 | ✅ Valid | **NEW from class notes** |

**Total: 421 implementation tasks across 15 proposals**

---

## Class Notes Integration

The following 3 additional proposals were created from class notes:

### 2. Refusal Templates UI ⭐ NEW
- **Why**: Supportive, empathetic refusals with resource links
- **Key Deliverables**: `config/refusal_templates.json`, `RefusalMessage.tsx` component
- **Pass Criteria**: All refusals show empathy + resource link

### 14. Alpha Test Protocol ⭐ NEW
- **Why**: Real user validation before broader release
- **Key Deliverables**: `docs/alpha_plan.md`, consent form, feedback system
- **Pass Criteria**: ≥80% "felt helpful", 0 P0 safety bugs

### 15. Demo & One-Pager ⭐ NEW
- **Why**: Stakeholder demonstration and metrics report
- **Key Deliverables**: 2-minute demo video, executive summary with metrics
- **Pass Criteria**: Demo reproducible via docker compose, metrics align with SLOs

---

## Quick Start Guide

### View All Proposals
```bash
cd exercise_11
openspec list
```

### View Specific Proposal
```bash
# Example: View refusal templates proposal
openspec show add-refusal-templates-ui
```

### Validate Proposals
```bash
# Validate all changes
openspec validate --changes --strict

# Validate specific change
openspec validate add-safety-scope-policy --strict
```

### Implementation Workflow

For each task (following OpenSpec Stage 2: Implementation):

1. **Read the proposal**
   ```bash
   openspec show add-safety-scope-policy
   ```

2. **Review tasks checklist**
   - Open `openspec/changes/add-safety-scope-policy/tasks.md`
   - Work through tasks sequentially

3. **Implement requirements**
   - Refer to `specs/safety-guardrails/spec.md` for requirements and scenarios
   - Write code to fulfill each requirement

4. **Update task checklist**
   - Mark completed tasks: `- [x]` in `tasks.md`

5. **When all tasks complete**
   ```bash
   # Archive the change (moves to archive/, updates specs/)
   openspec archive add-safety-scope-policy
   ```

---

## Proposal Highlights by Category

### 🛡️ Safety & Security (3 proposals)
1. **Safety & Scope Policy**: Red-team testing, refusal templates, classification rules (16 tasks)
2. **Refusal Templates UI**: Empathetic copy, resource links, supportive styling (28 tasks)
3. **Guardrails + HITL Queue**: PII/crisis/medical detection, mentor queue UI, <500ms routing (26 tasks)

### 📚 Accuracy & Quality (2 proposals)
4. **Curated RAG Pack**: Vector search, citations required, ≥90% citation rate SLO (25 tasks)
5. **Prompt Versioning**: Version control, changelog, snapshot tests, CI enforcement (25 tasks)

### 🚀 Performance & Scale (2 proposals)
6. **SSE Streaming**: First token <1.5s, real-time UI updates (22 tasks)
7. **SLOs & Observability**: OpenTelemetry, p95 ≤2.5s, failure rate ≤1% (25 tasks)

### 🧪 Testing & Quality (3 proposals)
8. **Playwright E2E Suite**: 10+ scenarios, refusal flow, HITL escalation (23 tasks)
9. **Load Testing**: K6 & Locust, throughput, latency, error rates (30 tasks)
10. **Alpha Test Protocol**: User testing, feedback collection, ≥80% helpful (46 tasks)

### 🐳 DevOps & Infrastructure (2 proposals)
11. **Docker & Health Checks**: Dockerfiles, compose, `/readyz` endpoint, ≤20s startup (25 tasks)
12. **CI/CD Pipelines**: Lint, test, build, deploy automation (25 tasks)

### 💰 Cost & Accessibility (2 proposals)
13. **Token/Cost Watchdog**: Per-turn tracking, budget caps, lite mode fallback (25 tasks)
14. **Accessibility**: WCAG AA, keyboard nav, ARIA, Axe testing (36 tasks)

### 📊 Deliverables (1 proposal)
15. **Demo & One-Pager**: 2-minute video, metrics report, reproducible demo (44 tasks)

---

## Recommended Implementation Order

### Phase 1: Foundation & Safety (Weeks 1-2)
1. **Safety & Scope Policy** ← Start here (critical safety baseline)
2. **Refusal Templates UI** ← Immediate follow-up
3. **Curated RAG Pack** ← Accuracy foundation
4. **Dockerize & Health Checks** ← Deployment readiness

### Phase 2: Core Features (Weeks 3-4)
5. **SSE Advice Streaming** ← Better UX
6. **Guardrails + HITL Queue** ← Advanced safety
7. **Prompt Versioning** ← Quality control

### Phase 3: Testing & Observability (Weeks 5-6)
8. **Playwright E2E Suite** ← Comprehensive testing
9. **SLOs & Observability** ← Production monitoring
10. **Load Testing** ← Scalability validation

### Phase 4: Polish & Launch (Weeks 7-8)
11. **CI/CD Pipelines** ← Automation
12. **Token/Cost Watchdog** ← Cost control
13. **Accessibility & UX Polish** ← Production ready
14. **Alpha Test Protocol** ← User testing (2 weeks)
15. **Demo & One-Pager** ← Final deliverable

---

## Key SLOs & Pass Criteria

| Metric | Target | Proposal | Status |
|--------|--------|----------|--------|
| P95 Latency | ≤ 2.5s | SLOs & Observability, Load Testing | To validate |
| Error Rate | ≤ 1% | SLOs & Observability, Load Testing | To validate |
| First Token | < 1.5s | SSE Streaming | To validate |
| Citation Rate | ≥ 90% | RAG Pack | To validate |
| Red-Team Pass | 100% | Safety Policy | To validate |
| Refusal Quality | 100% have empathy + link | Refusal Templates UI | To validate |
| HITL Routing | < 500ms | Guardrails + HITL | To validate |
| Docker Startup | ≤ 20s | Docker & Health Checks | To validate |
| Axe Violations | 0 critical | Accessibility | To validate |
| Alpha Helpful | ≥ 80% | Alpha Test Protocol | To validate |
| Alpha Safety | 0 P0 bugs | Alpha Test Protocol | To validate |
| Demo Duration | ≤ 2 min | Demo & One-Pager | To validate |

---

## Detailed Proposal Summaries

### 1. Safety & Scope Policy (16 tasks)
**Deliverables**: `docs/safety_scope.md`, `config/safety_policy.json`, backend guard hook, 20 red-team unit tests

**Pass Criteria**: 20 red-team prompts trigger correct refusal/redirect

**Key Requirements**:
- Request classification (in-scope vs out-of-scope)
- Refusal templates for medical, crisis, legal, therapy
- Policy configuration without code changes
- 100% red-team test coverage

---

### 2. Refusal Templates UI ⭐ NEW (28 tasks)
**Deliverables**: Supportive copy with empathy, resource links, `RefusalMessage.tsx` component

**Pass Criteria**: All refusals show empathy + clickable resource link

**Key Requirements**:
- Medical refusal → pediatrician referral
- Crisis refusal → 988 hotline, abuse hotline
- Legal refusal → legal aid
- Therapy refusal → therapist finder
- Distinct UI styling (warm, supportive)

---

### 3. Curated RAG Pack (25 tasks)
**Deliverables**: `rag/ingest.py`, `rag/index.json`, retrieval helper, citation rendering

**Pass Criteria**: In 10 sampled chats, ≥90% responses include ≥1 citation

**Key Requirements**:
- Document ingestion from AAP, CDC, peer-reviewed sources
- Vector search retrieval
- Citation generation in responses
- Citation UI badges (clickable)

---

### 4. SSE Advice Streaming (22 tasks)
**Deliverables**: Backend SSE endpoint, frontend consumer, streaming UI

**Pass Criteria**: First token arrives <1.5s (p95)

**Key Requirements**:
- `/api/coach/stream/{session_id}` SSE endpoint
- Token-by-token streaming
- Real-time UI updates
- Typewriter effect

---

### 5. Playwright E2E Suite (23 tasks)
**Deliverables**: `frontend/e2e/assistant.spec.ts` expanded to 10 scenarios

**Pass Criteria**: All scenarios green; asserts structure (empathy, 3 steps, citations, safety footer)

**Scenarios**: Screen time, bedtime, sibling conflict, motivation, ADHD-like guidance, medical refusal, crisis escalation, legal refusal

---

### 6. Docker & Health Checks (25 tasks)
**Deliverables**: `Dockerfile` (API), `Dockerfile.web` (Next), `docker-compose.yml`, `/healthz`, `/readyz`

**Pass Criteria**: `docker compose up` → both services healthy ≤20s

**Key Requirements**:
- Backend Dockerfile with Python 3.11
- Frontend Dockerfile with Node 18
- `/readyz` checks RAG index + API key
- Fast startup optimization

---

### 7. CI/CD Pipelines (25 tasks)
**Deliverables**: `.github/workflows/ci.yml`, `.github/workflows/cd.yml`

**Pass Criteria**: Red blocks merge; green tag auto-deploys to staging

**Key Requirements**:
- CI: lint, type-check, unit tests, e2e tests, build
- CD: deploy on version tags
- Branch protection rules
- CodeQL security scanning

---

### 8. SLOs & Observability (25 tasks)
**Deliverables**: OpenTelemetry spans, dashboard JSON exports

**Pass Criteria**: 15-min load test p95 ≤2.5s, failure ≤1%

**Key Requirements**:
- Spans for RAG retrieval, LLM calls, guardrails
- Latency, error rate, throughput metrics
- Dashboard exports
- SLO validation via load test

---

### 9. Guardrails + HITL Queue (26 tasks)
**Deliverables**: `backend/app/guardrails.py` (PII/crisis/medical), `web/app/(hitl)/queue.tsx`

**Pass Criteria**: Crisis prompts → HITL <500ms; mentor reply appears in parent chat

**Key Requirements**:
- PII detection (names, SSN, addresses)
- Crisis keywords (suicide, abuse, harm)
- Medical symptom detection
- Mentor queue UI
- Response routing to parent chat

---

### 10. Prompt Versioning & Snapshots (25 tasks)
**Deliverables**: `prompts/child_coach_v1.json`, `tests/snapshots/*`, changelog

**Pass Criteria**: Changing prompts without version bump fails CI

**Key Requirements**:
- Versioned prompt files
- Prompt changelog
- Snapshot tests
- CI version check
- Runtime version selection

---

### 11. Token/Cost Watchdog (25 tasks)
**Deliverables**: `billing/ledger.py`, budget caps, lite-mode fallback, nightly CSV, admin dashboard

**Pass Criteria**: Over-budget requests return lite-mode with notice; CSV generated daily

**Key Requirements**:
- Token and cost tracking per request
- Daily budget cap enforcement
- Lite mode fallback (cheaper model)
- Nightly reports
- Admin dashboard with sparklines

---

### 12. Load Testing (30 tasks)
**Deliverables**: Uses scaffolds in `load/k6/coach_scenario.js` and `load/locust/locustfile.py`

**Pass Criteria**: Report with throughput, p95, error rate; meets SLOs

**Key Requirements**:
- K6 scenarios (10, 50, 100 VUs)
- Locust scenarios with web UI
- Concurrent WebSocket testing
- SLO verification (p95 ≤2.5s, error ≤1%)

---

### 13. Accessibility & UX Polish (36 tasks)
**Deliverables**: Keyboard nav, ARIA roles, disclaimers, Axe tests

**Pass Criteria**: Axe scan has no critical issues

**Key Requirements**:
- Full keyboard navigation
- ARIA roles for chat (log, live regions)
- Color contrast ≥4.5:1
- Focus indicators
- AI disclaimer banner
- Screen reader compatibility

---

### 14. Alpha Test Protocol ⭐ NEW (46 tasks)
**Deliverables**: `docs/alpha_plan.md`, consent copy, feedback form, issue log

**Pass Criteria**: ≥80% "felt helpful", 0 P0 safety bugs

**Key Requirements**:
- Alpha test plan (10-20 testers, 2 weeks)
- Informed consent process
- Feedback form (helpfulness, trust, concerns)
- Issue tracking (P0/P1/P2)
- Post-test report

---

### 15. Demo & One-Pager ⭐ NEW (44 tasks)
**Deliverables**: 2-minute demo video, one-pager report

**Pass Criteria**: Demo reproducible from `docker compose up`; metrics align with SLOs

**Key Requirements**:
- 3 demo flows: refusal, normal advice with citations, HITL escalation
- Voiceover narration
- One-page report: metrics, risks, next steps
- Reproducible via `scripts/run_demo.sh`

---

## Next Steps

### For Implementation

1. **Pick a proposal** from the recommended order
2. **Read the full proposal**:
   ```bash
   cat openspec/changes/<change-id>/proposal.md
   cat openspec/changes/<change-id>/specs/*/spec.md
   ```
3. **Follow the task checklist**:
   ```bash
   cat openspec/changes/<change-id>/tasks.md
   ```
4. **Implement features** according to requirements
5. **Update tasks.md** as you complete items
6. **Test thoroughly** using scenarios from spec.md
7. **Archive when complete**:
   ```bash
   openspec archive <change-id>
   ```

### For Review

All proposals are ready for review. You can:
- Read through each proposal
- Provide feedback or request changes
- Adjust priorities
- Modify tasks or requirements

---

## OpenSpec Commands Reference

```bash
# List all changes
openspec list

# List specifications (empty until first archive)
openspec list --specs

# Show change details
openspec show <change-id>

# Show with JSON output
openspec show <change-id> --json --deltas-only

# Validate all changes
openspec validate --changes --strict

# Validate specific change
openspec validate <change-id> --strict

# Archive completed change
openspec archive <change-id>
```

---

## Files Created

### OpenSpec Structure
```
exercise_11/
├── openspec/
│   ├── AGENTS.md                          # Already existed
│   ├── project.md                         # ✅ Updated with project details
│   ├── changes/
│   │   ├── add-safety-scope-policy/
│   │   │   ├── proposal.md                # ✅ Created
│   │   │   ├── tasks.md                   # ✅ Created
│   │   │   └── specs/safety-guardrails/spec.md
│   │   ├── add-refusal-templates-ui/      # ⭐ NEW
│   │   │   ├── proposal.md                # ✅ Created
│   │   │   ├── tasks.md                   # ✅ Created
│   │   │   └── specs/safety-guardrails/spec.md
│   │   ├── add-curated-rag-pack/
│   │   ├── add-sse-advice-streaming/
│   │   ├── add-playwright-e2e-suite/
│   │   ├── add-docker-health-checks/
│   │   ├── add-cicd-pipelines/
│   │   ├── add-slos-observability/
│   │   ├── add-guardrails-hitl-queue/
│   │   ├── add-prompt-versioning-snapshots/
│   │   ├── add-token-cost-watchdog/
│   │   ├── add-load-testing/
│   │   ├── add-accessibility-ux-polish/
│   │   ├── add-alpha-test-protocol/       # ⭐ NEW
│   │   │   ├── proposal.md                # ✅ Created
│   │   │   ├── tasks.md                   # ✅ Created
│   │   │   └── specs/alpha-testing/spec.md
│   │   └── add-demo-and-onepager/         # ⭐ NEW
│   │       ├── proposal.md                # ✅ Created
│   │       ├── tasks.md                   # ✅ Created
│   │       └── specs/demo-deliverables/spec.md
│   └── specs/
│       └── (empty - will be populated after archiving changes)
```

---

## 🎉 Success Metrics

✅ **1 project.md** filled out with comprehensive details  
✅ **15 change proposals** created (12 original + 3 from class notes)  
✅ **15 capability specs** with requirements and scenarios  
✅ **421 implementation tasks** broken down and documented  
✅ **100% validation pass** rate with strict mode (15/15 passed)  
✅ **15 new capabilities** ready to implement  

---

## Support

- **OpenSpec Documentation**: See `openspec/AGENTS.md`
- **Project Context**: See `openspec/project.md`
- **Assignment Details**: See `exercise_11/README.md`

---

*Updated: 2025-11-01 (Added 3 proposals from class notes)*  
*Exercise 11 - Child Growth Assistant - Week 8*  
*15 proposals | 421 tasks | All validated ✅*
