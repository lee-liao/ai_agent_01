# Accessibility Capability

## ADDED Requirements

### Requirement: Keyboard Navigation
All interactive elements SHALL be accessible via keyboard.

#### Scenario: Tab navigation
- **WHEN** a user presses Tab
- **THEN** focus moves to the next interactive element
- **AND** focus order is logical

#### Scenario: Enter to submit
- **WHEN** a user types in the message input and presses Enter
- **THEN** the message is sent
- **AND** focus remains on the input

### Requirement: ARIA Roles and Labels
The interface SHALL include proper ARIA attributes for screen readers.

#### Scenario: Chat log role
- **WHEN** the chat container is rendered
- **THEN** it has `role="log"` and `aria-live="polite"`
- **AND** new messages are announced to screen readers

#### Scenario: Form labels
- **WHEN** form inputs are rendered
- **THEN** each has an `aria-label` or associated `<label>`

### Requirement: Color Contrast
Text SHALL meet WCAG AA contrast requirements.

#### Scenario: Normal text contrast
- **WHEN** measuring text/background contrast
- **THEN** ratio is ≥4.5:1 for normal text
- **AND** ≥3:1 for large text (18pt+)

### Requirement: Focus Indicators
Focused elements SHALL have visible focus indicators.

#### Scenario: Focus visibility
- **WHEN** an element receives keyboard focus
- **THEN** a 2px outline with high contrast is displayed
- **AND** the outline is visible on all backgrounds

### Requirement: AI Disclaimers
The interface SHALL display clear disclaimers about AI limitations.

#### Scenario: Disclaimer banner
- **WHEN** a user visits the chat page
- **THEN** a disclaimer is displayed: "AI-generated advice. Consult professionals for serious concerns."
- **AND** includes link to safety policy

#### Scenario: Refusal disclaimers
- **WHEN** a refusal message is shown
- **THEN** it includes a disclaimer and referral information

### Requirement: Axe Accessibility Scan
The application SHALL pass automated accessibility testing.

#### Scenario: Axe scan results
- **WHEN** Axe scan runs on key pages
- **THEN** there are no critical violations
- **AND** there are no serious violations

#### Scenario: Moderate issues documented
- **WHEN** moderate Axe violations are found
- **THEN** they are documented for future resolution
- **AND** do not block release

### Requirement: Screen Reader Compatibility
The application SHALL be usable with screen readers.

#### Scenario: Chat message announcement
- **WHEN** a new message arrives
- **THEN** screen readers announce the message content
- **AND** identify the speaker (parent/assistant/system)

