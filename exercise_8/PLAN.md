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

## Part 5: Multi-Agent Orchestration

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

## Part 6: Connecting and Finalizing

- [ ] **Implement the `replay` Function:**
    - [ ] Modify the `replay` function to re-run a workflow from the beginning.

- [ ] **Update API Endpoints to Use Redis:**
    - [ ] Go through all API endpoints and replace `BLACKBOARD` with Redis calls.