# Cost Management Capability

## ADDED Requirements

### Requirement: Token Usage Tracking
The system SHALL track tokens and costs for every LLM request.

#### Scenario: Log LLM usage
- **WHEN** an LLM request completes
- **THEN** prompt tokens, completion tokens, model, and cost are logged
- **AND** associated with session_id

#### Scenario: Calculate cost
- **WHEN** usage is logged
- **THEN** cost is calculated using model pricing (e.g., gpt-4: $0.03/1K prompt, $0.06/1K completion)

### Requirement: Budget Caps
The system SHALL enforce daily budget limits.

#### Scenario: Under budget
- **WHEN** daily spend is below `DAILY_BUDGET_USD`
- **THEN** requests use the default model
- **AND** processing proceeds normally

#### Scenario: Over budget
- **WHEN** daily spend exceeds `DAILY_BUDGET_USD`
- **THEN** requests use lite mode (cheaper model)
- **AND** response includes notice: "Using lite mode due to budget"

### Requirement: Lite Mode Fallback
The system SHALL provide a lower-cost mode when budget is exceeded.

#### Scenario: Lite mode activation
- **WHEN** budget is exceeded
- **THEN** the system switches to gpt-3.5-turbo (or equivalent)
- **AND** logs lite mode usage

### Requirement: Daily Reports
The system SHALL generate nightly cost reports.

#### Scenario: Report generation
- **WHEN** the nightly cron job runs
- **THEN** a CSV report is generated with: date, sessions, total_tokens, total_cost
- **AND** saved to `billing/reports/YYYY-MM-DD.csv`

#### Scenario: Report contents
- **WHEN** viewing a daily report
- **THEN** it includes per-session breakdown
- **AND** aggregates totals

### Requirement: Admin Dashboard
Admins SHALL have a dashboard to view cost metrics.

#### Scenario: Cost overview
- **WHEN** an admin visits `/admin/costs`
- **THEN** a sparkline shows daily spend for the last 30 days
- **AND** current budget utilization percentage is displayed

#### Scenario: Session cost ranking
- **WHEN** viewing the admin dashboard
- **THEN** top 10 sessions by cost are listed
- **AND** each shows tokens, cost, and timestamp

