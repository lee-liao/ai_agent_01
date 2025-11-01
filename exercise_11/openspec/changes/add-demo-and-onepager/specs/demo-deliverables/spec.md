# Demo Deliverables Capability

## ADDED Requirements

### Requirement: Two-Minute Demo Video
The project SHALL provide a 2-minute video demonstration of key capabilities.

#### Scenario: Demo flow coverage
- **WHEN** the demo video is played
- **THEN** it shows 3 distinct flows:
  - Refusal flow (out-of-scope question → empathetic refusal)
  - Normal advice flow (bedtime question → advice with citations)
  - HITL escalation flow (crisis mention → mentor response)
- **AND** total runtime ≤ 2 minutes

#### Scenario: Demo narration
- **WHEN** the demo plays
- **THEN** voiceover explains what's happening
- **AND** highlights key features (safety, citations, HITL)

### Requirement: Demo Reproducibility
The demo SHALL be reproducible via `docker compose up`.

#### Scenario: Clean startup
- **WHEN** running `docker compose up` on a fresh machine
- **THEN** all services start healthy
- **AND** the 3 demo flows work as shown in video
- **AND** no manual setup required (except env vars)

#### Scenario: Demo script
- **WHEN** executing `scripts/run_demo.sh`
- **THEN** the demo environment is set up automatically
- **AND** demo data is seeded if needed

### Requirement: One-Pager Report
The project SHALL provide a one-page executive summary report.

#### Scenario: Report structure
- **WHEN** reading `docs/one_pager.md`
- **THEN** it includes:
  - Executive summary (2-3 sentences)
  - Key metrics section
  - Safety & quality section
  - Risks section
  - Next steps section
- **AND** fits on one page (~500 words)

#### Scenario: Metrics section
- **WHEN** viewing the metrics section
- **THEN** it displays:
  - p95 latency (with SLO: ≤2.5s)
  - Failure rate (with SLO: ≤1%)
  - Citation rate (with SLO: ≥90%)
  - Cost per day (with budget)
- **AND** indicates if each metric meets SLO

### Requirement: Metrics Alignment
Report metrics SHALL align with measured SLOs.

#### Scenario: Metric validation
- **WHEN** metrics are published in one-pager
- **THEN** they are based on actual load test results
- **AND** citation rate is from real session sampling
- **AND** cost/day is from token tracking data
- **AND** no estimates or placeholder values

### Requirement: Risk Documentation
The report SHALL identify key risks.

#### Scenario: Risk section
- **WHEN** reading the risks section
- **THEN** it lists 3-5 concrete risks (e.g., cost escalation, RAG coverage gaps)
- **AND** each risk includes potential impact
- **AND** mitigation strategies are noted

### Requirement: Next Steps
The report SHALL define actionable next steps.

#### Scenario: Next steps section
- **WHEN** reading next steps
- **THEN** it includes 3-5 specific actions (e.g., expand RAG sources, beta launch plan)
- **AND** each has a suggested timeline
- **AND** priorities are clear

### Requirement: Demo Distribution
Demo assets SHALL be packaged for stakeholders.

#### Scenario: Demo package
- **WHEN** creating the demo package
- **THEN** it includes:
  - Demo video file (`demo/video.mp4`)
  - One-pager PDF
  - Setup instructions (`docs/demo_script.md`)
- **AND** is easily shareable (cloud link or email attachment)

