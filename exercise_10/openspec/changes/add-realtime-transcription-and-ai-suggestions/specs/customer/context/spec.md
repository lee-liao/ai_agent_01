## ADDED Requirements

### Requirement: Customer Context Panel
The system SHALL fetch and display customer info (profile, recent orders, tickets) at call start.

#### Scenario: Load Context on Call Start
- WHEN a call starts and a customer identifier is available
- THEN the frontend fetches customer details from the API
- AND displays name, email, LTV, recent orders, and tickets

