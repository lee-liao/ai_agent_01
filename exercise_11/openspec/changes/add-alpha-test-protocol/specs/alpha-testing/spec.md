# Alpha Testing Capability

## ADDED Requirements

### Requirement: Alpha Test Plan
The project SHALL have a documented alpha test plan.

#### Scenario: Plan contents
- **WHEN** reviewing `docs/alpha_plan.md`
- **THEN** it includes: objectives, tester criteria, duration, scenarios, success metrics
- **AND** defines bug severity levels (P0/P1/P2)

### Requirement: Informed Consent
Testers SHALL provide informed consent before participating.

#### Scenario: Consent form
- **WHEN** a tester is onboarded
- **THEN** they receive consent form explaining:
  - AI-generated advice limitations
  - Data collection and privacy
  - Right to withdraw
- **AND** must acknowledge consent before access

### Requirement: Feedback Collection
The system SHALL provide a feedback form for testers.

#### Scenario: Feedback form fields
- **WHEN** a tester submits feedback
- **THEN** the form captures:
  - Helpfulness rating (1-5 stars)
  - Ease of use rating
  - Trust level
  - Open comments
  - Safety concerns (flagged for urgent review)

#### Scenario: Feedback accessibility
- **WHEN** a tester wants to give feedback
- **THEN** a "Give Feedback" button is visible in the interface
- **AND** opens the feedback form

### Requirement: Issue Logging
Issues SHALL be logged and tracked with severity levels.

#### Scenario: Issue documentation
- **WHEN** an issue is identified
- **THEN** it is logged with: ID, severity (P0/P1/P2), description, status, resolution
- **AND** tracked in `docs/alpha_issues.md` or issue tracker

#### Scenario: P0 escalation
- **WHEN** a P0 safety bug is reported
- **THEN** an alert is sent to the team immediately
- **AND** triage begins within 1 hour

### Requirement: Helpfulness Target
The system SHALL achieve ≥80% "felt helpful" rating.

#### Scenario: Helpfulness calculation
- **WHEN** calculating helpfulness
- **THEN** count ratings of 4-5 stars as "helpful"
- **AND** percentage = (helpful count / total responses) × 100
- **AND** target ≥ 80%

### Requirement: Safety Bug Target
The alpha test SHALL identify zero P0 safety bugs.

#### Scenario: P0 safety bug definition
- **WHEN** categorizing bugs
- **THEN** P0 = bugs that could cause harm (e.g., dangerous advice, PII leak, failed refusal)

#### Scenario: Zero P0 requirement
- **WHEN** alpha test concludes
- **THEN** there are 0 unresolved P0 bugs
- **AND** any P0s found were fixed before test end

### Requirement: Tester Diversity
Testers SHALL represent diverse parent demographics.

#### Scenario: Tester recruitment
- **WHEN** recruiting 10-20 testers
- **THEN** include parents with children across age ranges (0-12 years)
- **AND** diverse backgrounds and experience levels

### Requirement: Post-Test Report
A summary report SHALL be generated after the alpha test.

#### Scenario: Report contents
- **WHEN** the alpha test concludes
- **THEN** the report includes:
  - Helpfulness percentage
  - Safety bug count (by severity)
  - Session count
  - Key feedback themes
  - Recommended improvements

