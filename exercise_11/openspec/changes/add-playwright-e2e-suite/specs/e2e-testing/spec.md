# E2E Testing Capability

## ADDED Requirements

### Requirement: Comprehensive Scenario Coverage
The E2E test suite SHALL cover at least 10 realistic parenting scenarios.

#### Scenario: Normal advice scenarios
- **WHEN** tests run for screen time, bedtime, sibling conflict, picky eating, tantrums, motivation
- **THEN** all 6 scenarios pass with valid advice responses

#### Scenario: Boundary scenarios
- **WHEN** tests run for ADHD-like behavior, medical questions, crisis situations, legal questions
- **THEN** all 4 scenarios correctly trigger refusal or escalation

### Requirement: Response Quality Assertions
Each test SHALL assert response structure includes empathy, steps, citations, and safety footer.

#### Scenario: Advice structure validation
- **WHEN** an advice response is received
- **THEN** the test asserts presence of empathy statement
- **AND** asserts 3 concrete action steps
- **AND** asserts at least 1 citation
- **AND** asserts safety disclaimer footer

### Requirement: WebSocket Interaction Testing
Tests SHALL validate real-time WebSocket communication.

#### Scenario: Message exchange
- **WHEN** user sends a message via WebSocket
- **THEN** the test waits for response
- **AND** validates response arrives within timeout
- **AND** checks message format is correct

### Requirement: CI Integration
E2E tests SHALL run in CI and block merges on failure.

#### Scenario: PR test gate
- **WHEN** a pull request is opened
- **THEN** Playwright tests run automatically
- **AND** PR cannot merge until all tests are green
- **AND** test artifacts are uploaded on failure

