# Prompt Versioning Capability

## ADDED Requirements

### Requirement: Versioned Prompt Files
Prompts SHALL be stored as versioned JSON files.

#### Scenario: Prompt file structure
- **WHEN** a prompt file is created
- **THEN** it includes: version, author, date, description, template
- **AND** follows naming convention `child_coach_vX.json`

#### Scenario: Version increments
- **WHEN** a prompt is modified
- **THEN** the version number is incremented
- **AND** a new file is created (e.g., v1 → v2)

### Requirement: Prompt Changelog
Changes SHALL be documented in a changelog.

#### Scenario: Changelog entry
- **WHEN** a new prompt version is created
- **THEN** `prompts/CHANGELOG.md` is updated
- **AND** includes: version, date, author, summary of changes

### Requirement: Snapshot Testing
The system SHALL use snapshot tests to detect unintended prompt changes.

#### Scenario: Snapshot comparison
- **WHEN** snapshot tests run
- **THEN** actual LLM outputs are compared to snapshots
- **AND** tests fail if outputs don't match

#### Scenario: Intentional prompt update
- **WHEN** prompts are intentionally changed
- **THEN** snapshots are updated manually
- **AND** version is incremented

### Requirement: CI Version Check
CI SHALL fail if prompts change without version increment.

#### Scenario: Prompt changed without version bump
- **WHEN** a prompt file is modified without version increment
- **THEN** CI fails with error message
- **AND** PR cannot be merged

#### Scenario: Prompt changed with version bump
- **WHEN** a prompt file is modified AND version is incremented
- **THEN** CI passes
- **AND** changelog is required

### Requirement: Runtime Version Selection
The system SHALL support loading specific prompt versions.

#### Scenario: Default to latest
- **WHEN** no `PROMPT_VERSION` is set
- **THEN** the system loads the highest version number

#### Scenario: Load specific version
- **WHEN** `PROMPT_VERSION=1` is set
- **THEN** the system loads `child_coach_v1.json`
- **AND** logs the active version on startup

