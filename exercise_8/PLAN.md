# Implementation Plan

This document outlines the plan for implementing the backend of the HITL Contract Redlining Orchestrator.

## Current Status

- [x] Core review, replay, and HITL workflows implemented end-to-end.
- [ ] Reports page testing and verification outstanding.
- [ ] Future development initiatives (see “Future Development”) queued for subsequent phases.

## Part 1: Foundations & Setup

- [x] **Integrate Redis for the Blackboard:**
    - [x] Add Redis service to `docker-compose.yml`.
    - [x] Add `redis` to `backend/requirements.txt`.
    - [x] Update `backend/app/main.py` to use Redis.

- [x] **Implement Document Parsing with custom implementation (replacing MinerU):**
    - [x] Add `PyPDF2` and `python-docx` to `backend/requirements.txt`.
    - [x] Update `upload_doc` with custom document parsing for PDF, DOCX, DOC, MD, TXT formats with clause extraction.

- [x] **Configure OpenAI for Risk Assessment:**
    - [x] Add `openai` to `backend/requirements.txt`.
    - [x] Add OpenAI API Key to `docker-compose.yml`.
    - [x] Initialize OpenAI client in `backend/app/main.py`.

## Part 2: Add PostgreSQL Database

- [x] **Add PostgreSQL service to `docker-compose.yml`:**
    - [x] Use the `pgvector/pgvector:pg15` image.
    - [x] Configure the database, user, and password.
    - [x] Set up a volume for data persistence.

## Part 3: Adopt Reusable Components from Exercise 7

- [x] **Adopt Observability Stack:**
    - [x] Copy `observability` directory from `exercise_7` to `exercise_8`.
    - [x] Integrate `setup_observability` into `backend/app/main.py`.
    - [x] Note: The `jaeger`, `otel-collector`, `prometheus`, and `grafana` containers from `exercise_7` will be used. They will not be added to `exercise_8/docker-compose.yml`.
- [x] **Adopt Reusable Backend Utilities:**
    - [x] Copy `backend/app/utils` directory from `exercise_7` to `exercise_8/backend/app`.
    - [x] Implement logging using `setup_app_logging`.
    - [x] Copy `backend/app/config.py` and `backend/app/database.py` and adapt for `exercise_8`.
    - [x] Copy `.env` from `exercise_7/backend` to `exercise_8/backend`.
    - [x] Add required dependancies to `backend/requirements.txt` when copying the programs.
- [x] **Adopt Health Check Endpoints:**
    - [x] Add `/health` and `/health/detailed` endpoints to `backend/app/main.py`.
- [x] **Adopt CORS Middleware:**
    - [x] Add CORS middleware to `backend/app/main.py`.

## Part 4: Frontend Reusable Components

- [x] **Create a `ui` directory in `frontend/src/components`.**
- [x] **Implement `PageHeader.tsx`:**
    - [x] Create a component for the title and description.
    - [x] Refactor pages to use `PageHeader`.
- [x] **Implement `Card.tsx`:**
    - [x] Create a container component for content blocks.
    - [x] Refactor pages to use `Card`.
- [x] **Implement `Button.tsx`:**
    - [x] Create a general-purpose button component with variants.
    - [x] Refactor pages to use `Button`.
- [x] **Implement `RadioGroup.tsx`:**
    - [x] Create a component for the styled radio button groups.
    - [x] Refactor `run/page.tsx` to use `RadioGroup`.
- [x] **Implement `Dropzone.tsx`:**
    - [x] Create a reusable file dropzone component.
    - [x] Refactor `documents/page.tsx` to use `Dropzone`.
- [x] **Implement `EmptyState.tsx`:**
    - [x] Create a component to show when a list is empty.
    - [x] Refactor `documents/page.tsx` to use `EmptyState`.

## Part 5: Core Document Processing & Risk Assessment

- [x] **Enhance Document Parsing:**
    - [x] Parse uploaded documents into structured clauses with headings and body text
    - [x] Handle different document formats (PDF, DOCX, Markdown, TXT) properly
    - [x] Store parsed clauses in the blackboard with proper structure
    - [x] Test document upload and parsing via UI

- [x] **Implement Risk Assessment Logic:**
    - [x] Create function to compare clauses against policy rules
    - [x] Implement risk scoring algorithm (HIGH/MEDIUM/LOW)
    - [x] Generate rationale for each risk assessment
    - [x] Create policy reference mapping
    - [x] Test risk assessments via UI

## Part 6: Multi-Agent Orchestration

- [x] **Implement the Orchestration Logic in `start_run`:**
    - [x] Create a dispatcher in `start_run` to call the correct agent workflow based on `agent_path`.

- [x] **Implement the Agent Workflows:**
    - [x] **Manager-Worker Workflow:**
        - [x] Create `manager_worker_workflow` function.
        - [x] Implement Manager logic to retrieve clauses and create tasks.
        - [x] Implement Worker logic to process clauses in parallel using `ThreadPoolExecutor`.
        - [x] Implement `risk_analyzer` function to call OpenAI API.
    - [x] **Planner-Executor Workflow:**
        - [x] Create `planner_executor_workflow` function.
        - [x] Implement Planner logic to define a plan.
        - [x] Implement Executor logic to run the plan and save checkpoints to Redis.
    - [x] **Reviewer/Referee Workflow:**
        - [x] Create `reviewer_referee_workflow` function.
        - [x] Implement Reviewer logic to check assessments against a checklist.
        - [x] Implement Referee logic to flag contested assessments for HITL.
    - [x] Test each agent workflow via UI

## Part 7: Redline Generation & HITL Gates

- [x] **Implement Redline Proposal Generator:**
    - [x] Identify clauses that need redlining based on risk assessment
    - [x] Generate alternative text for risky clauses
    - [x] Create before/after comparison views
    - [x] Include rationale and policy references in redline proposals
    - [x] Store proposals in the blackboard with proper metadata
    - [x] Test redline generation via UI

- [x] **Enhance HITL Gates:**
    - [x] Implement risk approval workflow with proper UI integration
    - [x] Track human decisions accurately
    - [x] Implement final approval workflow with proper UI integration
    - [x] Test both HITL gates via UI

## Part 8: Export Functionality

- [x] **Implement Document Export Features:**
    - [x] Create DOCX export with redline markup
    - [x] Create PDF summary memo generator
    - [x] Create Markdown export with changes highlighted
    - [x] Generate CSV decision cards with all assessments and proposals (implemented as part of broader export functionality)
    - [x] Add proper formatting for legal document standards
    - [x] Test export functionality via UI

## Part 9: Metrics, Observability & Tool Routing

- [x] **Implement Cost Tracking:**
    - [x] Track API usage costs (OpenAI, etc.)
    - [x] Calculate cost per run, document, and agent path
    - [x] Store cost metrics in the system (via metrics module)

- [x] **Implement Quality Metrics:**
    - [x] Track pass rate and precision metrics
    - [x] Calculate mitigation rates
    - [x] Store and report quality indicators
    - [x] Implement SLO monitoring (latency, quality, cost)
    - [x] Test metrics reporting via UI

- [x] **Implement Tool Routing Logic:**
    - [x] Implement decision logic between policy lookup vs LLM-based analysis
    - [x] Create dynamic tool composition
    - [x] Optimize policy lookup for common cases
    - [x] Implement fallback mechanisms

## Part 10: Production Patterns & Final Integration

- [x] **Error Handling & Production Features:**
    - [x] Implement proper error handling and recovery
    - [x] Add circuit breakers for external calls
    - [x] Implement retry logic with exponential backoff
    - [x] Add rate limiting and throttling

- [x] **Enhanced Replay & Debug Functionality:**
    - [x] Enhance replay functionality beyond simple cloning
    - [x] Allow modification of inputs for what-if scenarios
    - [x] Implement proper step-by-step trace viewing
    - [x] Add comparison between original and replay runs

- [x] **Implement the `replay` Function:**
    - [x] Modify the `replay` function to re-run a workflow from the beginning.

- [x] **Update API Endpoints to Use Redis:**
    - [x] Go through all API endpoints and replace `BLACKBOARD` with Redis calls.

- [x] **Final Testing & Integration:**
    - [x] Complete end-to-end testing of all features
    - [x] Verify all UI pages work with backend implementation
    - [x] Test all success criteria from README

## Part 11: Multi-Agent Framework Adoption

- [x] **Analyze and Integrate New Framework:**
    - [x] Review new multi-agent framework components (Agent, Team, Coordinator)
    - [x] Assess compatibility with existing implementation
    - [x] Create integration plan for new framework with existing system
    - [x] Update PLAN.md with framework adoption tasks

- [x] **Framework Integration:**
    - [x] Replace current agent system with new Agent/Team/Coordinator architecture
    - [x] Migrate existing functionality to use new agent patterns
    - [x] Integrate new framework with existing Redis storage
    - [x] Ensure API compatibility with frontend components

- [x] **Agent Enhancement:**
    - [x] Complete implementation of ParserAgent with advanced clause extraction
    - [x] Complete implementation of RiskAnalyzerAgent with sophisticated risk assessment
    - [x] Complete implementation of RedlineGeneratorAgent with proper proposal generation
    - [x] Implement ReviewerAgent for checklist-driven validation
    - [x] Implement RefereeAgent for contested decision arbitration

- [x] **Team Pattern Implementation:**
    - [x] Complete parallel execution with ThreadPoolExecutor or asyncio
    - [x] Implement proper Manager-Worker pattern with task decomposition
    - [x] Enhance Pipeline pattern with proper data passing between agents
    - [x] Add checkpoint/recovery functionality for run persistence

- [x] **Enhanced Orchestration:**
    - [x] Integrate HITL gates with new coordinator pattern
    - [x] Enhance run lifecycle management
    - [x] Implement advanced debugging and replay functionality
    - [x] Add comprehensive execution history tracking

## Part 12: Document Structuring & Clause Quality

- [x] **Integrate shared clause parsing:**
    - [x] Delegate `ParserAgent` clause extraction to `parse_document_content` for consistent heading detection.
    - [x] Normalize clause IDs, headings, and text content for downstream agents.

- [x] **Hierarchical Clause Extraction:**
    - [x] Update parsing pipeline to capture section/subsection hierarchy for nested numbering schemes.
    - [x] Preserve heading metadata needed by Reviewer/Risk agents.
    - [x] Keep parser configurable for diverse legal formats.

## Part 13: HITL Risk Review Data Flow

- [x] **Replace Risk Gate mocks with live data:**
    - [x] Expose `/api/hitl/pending-runs` and `/api/hitl/runs/{run_id}/assessments` endpoints with enriched data.
    - [x] Update frontend Risk Gate page to load pending runs/assessments and submit real approvals.
    - [x] Add automated tests covering risk run summaries, assessments, and approval lifecycle.

- [x] **Persist Risk Gate approval decisions:**
    - [x] Define storage layer for assessor decisions (reuse PostgreSQL or blackboard persistence as appropriate).
    - [x] Update backend HITL endpoints to write/read approval state per assessment.
    - [x] Ensure frontend submits decisions and rehydrates persisted statuses on load.
    - [x] Add automated regression tests covering refresh scenarios and bulk approval flows.

- [x] **Finalize redline approval flow:**
    - [x] Surface redline proposals and summaries for Final Approval gate.
    - [x] Update coordinator metadata so downstream endpoints expose proposals consistently.
    - [x] Verify Final Approval UI reflects persisted proposal decisions end-to-end.

- [ ] **Expand Risk Gate gating criteria:**
    - [ ] Update coordinator approval gating to include medium/low risk clauses per policy.
    - [ ] Ensure pending runs endpoint surfaces runs without high risks.
    - [ ] Adjust UI cues to reflect broader approval scope.

- [ ] **Operational Verification:**
    - [ ] Perform manual HITL walkthroughs in staging to validate UX and edge cases.
    - [ ] Capture follow-up issues and polish items from manual review.

## Part 14: Team & Run Persistence Enhancements

- [x] **Persist Team Definitions to JSON:**
    - [x] Store configured teams in `exercise_8/data/team` as a JSON file that mirrors the coordinator’s registered teams.
    - [x] Load teams from the JSON file during startup to recreate coordinator state when Redis/DB is empty.

- [ ] **Run Execution Trace Persistence:**
    - [ ] Design PostgreSQL schema (`run_instances`, `run_events`, `run_artifacts`, optional `run_metrics`).
    - [ ] Implement repository layer for inserting runs, appending events, storing artifacts, and querying timelines.
    - [ ] Update coordinator lifecycle to persist run start/finish, agent steps, blackboard checkpoints, and failure reasons.
    - [ ] Ensure Redis continues serving latest state while Postgres becomes source of truth for history.

- [ ] **Replay Workflow:**
    - [x] Add API endpoint to clone a run with overrides, seeded from stored inputs/artifacts.
    - [x] Allow coordinator to bootstrap from persisted state and link replay runs back to their original.
    - [x] Expose APIs for fetching timelines, replay lineage, and comparisons for frontend consumption.
    - [x] Support "what-if" scenarios where users edit an individual step’s LLM prompt/input and replay from that point forward.
    - [x] Surface replay vs original comparisons for score, duration, risk counts, and cost metrics.

- [ ] **Testing & Observability:**
    - [ ] Add automated tests around persistence and replay flows.
    - [ ] Emit structured logs/metrics for run and replay outcomes to aid debugging.

## Part 15: Verification & End-to-End Testing

- [ ] **Automated Verification Harness:**
    - [ ] Stand up pytest suites that spin up Redis/Postgres test instances and seed sample documents.
    - [ ] Provide helper factories to create documents, playbooks, and run requests for reuse across tests.

- [ ] **Core E2E Scenarios:**
    - [ ] Upload document → start `sequential` run → verify assessments/proposals persisted and rendered via API.
    - [ ] Execute `manager_worker` path with induced clause failures → ensure error events and failure reasons are stored.
    - [ ] Walk through Risk Gate approval flow (approve/reject mix) and confirm status transitions + audit trail.
    - [ ] Complete Final Approval and export workflow; confirm artifacts recorded and downloadable.
    - [ ] Trigger replay with modified agent path/options, validate linkage to original run and compare outcomes.

- [ ] **Reports Page Validation:**
    - [ ] Exercise the Reports experience end-to-end and confirm metrics align with backend data.
    - [ ] Capture any regressions or UX issues for follow-up fixes.

- [ ] **Manual Test Playbook (for HITL review):**
    - [ ] Document step-by-step verification instructions for operators (including UI checkpoints and expected metrics).
    - [ ] Include negative scenarios (missing teams, database outage, Redis miss) with rollback expectations.

## Future Development

- [ ] **Redis Clause Cache:**
    - [ ] Persist parsed clause texts into Redis so all agents can access a shared cache during review workflows.
    - [ ] Define cache invalidation and run-specific scoping to keep blackboard state aligned with Redis copies.
    - [ ] Evaluate performance implications and fallback handling when Redis is unavailable.
- [ ] **Persist Teams in Database:**
    - [ ] Store team definitions in PostgreSQL for durability beyond JSON files.
    - [ ] Provide migration scripts and admin APIs to manage team configurations centrally.
    - [ ] Keep Redis/blackboard synchronization consistent when team records change.
- [ ] **Persist Risk Gate decisions durably:**
    - [ ] Design schema to store clause-level risk approvals/comments in Postgres.
    - [ ] Synchronize coordinator blackboard state with durable records on read/write.
    - [ ] Update APIs to source persisted decisions so reviewers retain history across restarts.
- [ ] **Replay What-If enhancements:**
    - [ ] Redesign agent-path switching workflow for Replay before implementation.