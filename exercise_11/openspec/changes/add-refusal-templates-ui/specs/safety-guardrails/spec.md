# Safety Guardrails Enhancement: Refusal Templates UI

## MODIFIED Requirements

### Requirement: Refusal Templates
The system SHALL provide supportive, empathetic refusal templates for each out-of-scope category.

#### Scenario: Medical refusal with empathy and resources
- **WHEN** a medical diagnosis request is refused
- **THEN** the response includes:
  - Empathy statement acknowledging parent's concern
  - Clear explanation of why this is out of scope
  - Link to "Find a Pediatrician" resource
  - Suggestion to call doctor's office

#### Scenario: Crisis refusal with immediate resources
- **WHEN** a crisis situation is detected
- **THEN** the response includes:
  - Empathy statement validating distress
  - 988 Suicide & Crisis Lifeline (clickable)
  - National Child Abuse Hotline: 1-800-422-4453 (clickable)
  - Local emergency services (911)
  - Encouragement to reach out immediately

#### Scenario: Legal refusal with referrals
- **WHEN** a legal question is refused
- **THEN** the response includes:
  - Empathy statement
  - Explanation that legal advice requires attorney
  - Link to Legal Aid Society
  - Suggestion for family law consultation

#### Scenario: Therapy refusal with counselor referral
- **WHEN** a therapy-level concern is detected
- **THEN** the response includes:
  - Validation of parent's feelings
  - Explanation that deeper support may help
  - Link to "Find a Therapist" (Psychology Today)
  - Encouragement that seeking help is strength

### Requirement: Refusal UI Rendering
The frontend SHALL render refusal messages with distinct, supportive styling.

#### Scenario: Refusal message component
- **WHEN** a refusal message is displayed
- **THEN** it uses a dedicated `RefusalMessage` component
- **AND** has warm color scheme (not harsh red)
- **AND** displays empathy statement prominently
- **AND** shows resource links as interactive buttons/cards

#### Scenario: Resource links are clickable
- **WHEN** a refusal includes resource links
- **THEN** each link is clickable and opens in new tab
- **AND** has clear label (e.g., "Call 988 Crisis Lifeline")
- **AND** includes icon for phone numbers vs websites

### Requirement: Universal Refusal Quality
ALL refusals SHALL include empathy + at least one resource link.

#### Scenario: Refusal validation
- **WHEN** testing all refusal categories
- **THEN** every refusal contains:
  - An empathy or validation statement
  - At least one actionable resource (link or phone number)
  - Supportive tone throughout
  - No judgment or dismissiveness

