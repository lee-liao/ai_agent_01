# customer-context Specification

## Purpose
TBD - created by archiving change add-public-customer-context. Update Purpose after archive.
## Requirements
### Requirement: Public Customer Context Lookup
The system SHALL provide a read-only public endpoint to return limited customer context for the customer chat UI.

#### Scenario: Search by Basic Identifiers
- WHEN querying `/api/customers/public/search?q=<text>`
- THEN the API searches by name, email, phone, or account number
- AND returns limited fields: name, email, phone, account_number, tier, status, and recent (<=10) orders/tickets

#### Scenario: No Match
- WHEN no customer matches
- THEN the API returns `null` with 200 OK

#### Scenario: Security Constraints
- GIVEN this is public
- THEN exclude sensitive fields; return only non-sensitive context

