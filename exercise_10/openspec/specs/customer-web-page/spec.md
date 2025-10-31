# customer-web-page Specification

## Purpose
TBD - created by archiving change add-customer-web-page. Update Purpose after archive.
## Requirements
### Requirement: Unified Styling With Call Center UI
The customer web pages SHALL use the same design system and visual language as the agent Call Center UI.

#### Scenario: Shared Theme Tokens
- GIVEN Tailwind theme tokens in `tailwind.config.js`
- WHEN rendering customer pages
- THEN colors, typography, and spacing use the shared tokens (e.g., `primary.*`), not ad-hoc inline styles

#### Scenario: Consistent Components
- GIVEN common UI patterns (headers, buttons, cards)
- WHEN rendering customer pages
- THEN components match the agent UI style (rounded, shadows, icon set) for a cohesive look

#### Scenario: Brand Consistency
- WHEN viewing customer vs agent pages
- THEN primary color, typography scale, and iconography are consistent across both experiences

