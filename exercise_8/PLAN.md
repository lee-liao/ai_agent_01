# Implementation Plan

This document outlines the plan for implementing the backend of the HITL Contract Redlining Orchestrator.

## Part 1: Foundations & Setup

- [ ] **Integrate Redis for the Blackboard:**
    - [ ] Add Redis service to `docker-compose.yml`.
    - [ ] Add `redis` to `backend/requirements.txt`.
    - [ ] Update `backend/app/main.py` to use Redis.

- [ ] **Implement Document Parsing with MinerU:**
    - [ ] Add `mineru[core]` to `backend/requirements.txt`.
    - [ ] Update `upload_doc` to use MinerU for parsing.

- [ ] **Configure OpenAI for Risk Assessment:**
    - [ ] Add `openai` to `backend/requirements.txt`.
    - [ ] Add OpenAI API Key to `docker-compose.yml`.
    - [ ] Initialize OpenAI client in `backend/app/main.py`.

## Part 2: Add PostgreSQL Database

- [ ] **Add PostgreSQL service to `docker-compose.yml`:**
    - [ ] Use the `pgvector/pgvector:pg15` image.
    - [ ] Configure the database, user, and password.
    - [ ] Set up a volume for data persistence.

## Part 3: Adopt Reusable Components from Exercise 7

- [ ] **Adopt Observability Stack:**
    - [ ] Copy `observability` directory from `exercise_7` to `exercise_8`.
    - [ ] Integrate `setup_observability` into `backend/app/main.py`.
    - [ ] Note: The `jaeger`, `otel-collector`, `prometheus`, and `grafana` containers from `exercise_7` will be used. They will not be added to `exercise_8/docker-compose.yml`.
- [ ] **Adopt Reusable Backend Utilities:**
    - [ ] Copy `backend/app/utils` directory from `exercise_7` to `exercise_8/backend/app`.
    - [ ] Implement logging using `setup_app_logging`.
    - [ ] Copy `backend/app/config.py` and `backend/app/database.py` and adapt for `exercise_8`.
    - [ ] Copy `.env` from `exercise_7/backend` to `exercise_8/backend`.
    - [ ] Add required dependancies to `backend/requirements.txt` when copying the programs.
- [ ] **Adopt Health Check Endpoints:**
    - [ ] Add `/health` and `/health/detailed` endpoints to `backend/app/main.py`.
- [ ] **Adopt CORS Middleware:**
    - [ ] Add CORS middleware to `backend/app/main.py`.

## Part 4: Frontend Reusable Components

- [ ] **Create a `ui` directory in `frontend/src/components`.**
- [ ] **Implement `PageHeader.tsx`:**
    - [ ] Create a component for the page title and description.
    - [ ] Refactor pages to use `PageHeader`.
- [ ] **Implement `Card.tsx`:**
    - [ ] Create a container component for content blocks.
    - [ ] Refactor pages to use `Card`.
- [ ] **Implement `Button.tsx`:**
    - [ ] Create a general-purpose button component with variants.
    - [ ] Refactor pages to use `Button`.
- [ ] **Implement `RadioGroup.tsx`:**
    - [ ] Create a component for the styled radio button groups.
    - [ ] Refactor `run/page.tsx` to use `RadioGroup`.
- [ ] **Implement `Dropzone.tsx`:**
    - [ ] Create a reusable file dropzone component.
    - [ ] Refactor `documents/page.tsx` to use `Dropzone`.
- [ ] **Implement `EmptyState.tsx`:**
    - [ ] Create a component to show when a list is empty.
    - [ ] Refactor `documents/page.tsx` to use `EmptyState`.

## Part 5: Core Document Processing & Risk Assessment

- [ ] **Enhance Document Parsing:**
    - [ ] Parse uploaded documents into structured clauses with headings and body text
    - [ ] Handle different document formats (PDF, DOCX, Markdown, TXT) properly
    - [ ] Store parsed clauses in the blackboard with proper structure
    - [ ] Test document upload and parsing via UI

- [ ] **Implement Risk Assessment Logic:**
    - [ ] Create function to compare clauses against policy rules
    - [ ] Implement risk scoring algorithm (HIGH/MEDIUM/LOW)
    - [ ] Generate rationale for each risk assessment
    - [ ] Create policy reference mapping
    - [ ] Test risk assessments via UI

## Part 6: Multi-Agent Orchestration

- [ ] **Implement the Orchestration Logic in `start_run`:**
    - [ ] Create a dispatcher in `start_run` to call the correct agent workflow based on `agent_path`.

- [ ] **Implement the Agent Workflows:**
    - [ ] **Manager-Worker Workflow:**
        - [ ] Create `manager_worker_workflow` function.
        - [ ] Implement Manager logic to retrieve clauses and create tasks.
        - [ ] Implement Worker logic to process clauses in parallel using `ThreadPoolExecutor`.
        - [ ] Implement `risk_analyzer` function to call OpenAI API.
    - [ ] **Planner-Executor Workflow:**
        - [ ] Create `planner_executor_workflow` function.
        - [ ] Implement Planner logic to define a plan.
        - [ ] Implement Executor logic to run the plan and save checkpoints to Redis.
    - [ ] **Reviewer/Referee Workflow:**
        - [ ] Create `reviewer_referee_workflow` function.
        - [ ] Implement Reviewer logic to check assessments against a checklist.
        - [ ] Implement Referee logic to flag contested assessments for HITL.
    - [ ] Test each agent workflow via UI

## Part 7: Redline Generation & HITL Gates

- [ ] **Implement Redline Proposal Generator:**
    - [ ] Identify clauses that need redlining based on risk assessment
    - [ ] Generate alternative text for risky clauses
    - [ ] Create before/after comparison views
    - [ ] Include rationale and policy references in redline proposals
    - [ ] Store proposals in the blackboard with proper metadata
    - [ ] Test redline generation via UI

- [ ] **Enhance HITL Gates:**
    - [ ] Implement risk approval workflow with proper UI integration
    - [ ] Track human decisions accurately
    - [ ] Implement final approval workflow with proper UI integration
    - [ ] Test both HITL gates via UI

## Part 8: Export Functionality

- [ ] **Implement Document Export Features:**
    - [ ] Create DOCX export with redline markup
    - [ ] Create PDF summary memo generator
    - [ ] Create Markdown export with changes highlighted
    - [ ] Generate CSV decision cards with all assessments and proposals
    - [ ] Add proper formatting for legal document standards
    - [ ] Test export functionality via UI

## Part 9: Metrics, Observability & Tool Routing

- [ ] **Implement Cost Tracking:**
    - [ ] Track API usage costs (OpenAI, etc.)
    - [ ] Calculate cost per run, document, and agent path
    - [ ] Store cost metrics in the database

- [ ] **Implement Quality Metrics:**
    - [ ] Track pass rate and precision metrics
    - [ ] Calculate mitigation rates
    - [ ] Store and report quality indicators
    - [ ] Implement SLO monitoring (latency, quality, cost)
    - [ ] Test metrics reporting via UI

- [ ] **Implement Tool Routing Logic:**
    - [ ] Implement decision logic between policy lookup vs LLM-based analysis
    - [ ] Create dynamic tool composition
    - [ ] Optimize policy lookup for common cases
    - [ ] Implement fallback mechanisms

## Part 10: Production Patterns & Final Integration

- [ ] **Error Handling & Production Features:**
    - [ ] Implement proper error handling and recovery
    - [ ] Add circuit breakers for external calls
    - [ ] Implement retry logic with exponential backoff
    - [ ] Add rate limiting and throttling

- [ ] **Enhanced Replay & Debug Functionality:**
    - [ ] Enhance replay functionality beyond simple cloning
    - [ ] Allow modification of inputs for what-if scenarios
    - [ ] Implement proper step-by-step trace viewing
    - [ ] Add comparison between original and replay runs

- [ ] **Implement the `replay` Function:**
    - [ ] Modify the `replay` function to re-run a workflow from the beginning.

- [ ] **Update API Endpoints to Use Redis:**
    - [ ] Go through all API endpoints and replace `BLACKBOARD` with Redis calls.

- [ ] **Final Testing & Integration:**
    - [ ] Complete end-to-end testing of all features
    - [ ] Verify all UI pages work with backend implementation
    - [ ] Test all success criteria from README