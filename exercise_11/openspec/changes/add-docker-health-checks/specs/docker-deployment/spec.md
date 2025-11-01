# Docker Deployment Capability

## ADDED Requirements

### Requirement: Backend Container
The system SHALL provide a Dockerfile for the backend API.

#### Scenario: Backend image build
- **WHEN** `docker build -f Dockerfile -t coach-backend .` is run
- **THEN** the image builds successfully
- **AND** includes all Python dependencies
- **AND** is optimized for size (<500MB)

### Requirement: Frontend Container
The system SHALL provide a Dockerfile for the Next.js frontend.

#### Scenario: Frontend image build
- **WHEN** `docker build -f Dockerfile.web -t coach-frontend .` is run
- **THEN** the image builds successfully
- **AND** includes production Next.js build
- **AND** is optimized for size (<300MB)

### Requirement: Docker Compose Orchestration
The system SHALL provide docker-compose configuration for local development.

#### Scenario: Start all services
- **WHEN** `docker compose up` is run
- **THEN** both backend and frontend services start
- **AND** both become healthy within 20 seconds
- **AND** services can communicate

### Requirement: Readiness Checks
The `/readyz` endpoint SHALL verify system dependencies before accepting traffic.

#### Scenario: System ready
- **WHEN** `/readyz` is called and RAG index exists and API key is set
- **THEN** return 200 with `{"status": "ready"}`

#### Scenario: RAG index missing
- **WHEN** `/readyz` is called and RAG index does not exist
- **THEN** return 503 with `{"status": "not_ready", "reason": "RAG index not found"}`

#### Scenario: API key missing
- **WHEN** `/readyz` is called and OPENAI_API_KEY is not set
- **THEN** return 503 with `{"status": "not_ready", "reason": "OpenAI API key not configured"}`

### Requirement: Fast Startup
Services SHALL reach healthy status within 20 seconds.

#### Scenario: Startup time measurement
- **WHEN** `docker compose up` is run from clean state
- **THEN** backend /readyz returns 200 within 15 seconds
- **AND** frontend responds within 20 seconds

