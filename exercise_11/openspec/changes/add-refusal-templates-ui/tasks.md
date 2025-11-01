# Implementation Tasks

## 1. Refusal Template Content
- [ ] 1.1 Write empathetic medical refusal template with pediatrician referral
- [ ] 1.2 Write crisis refusal template with hotline numbers (988, local resources)
- [ ] 1.3 Write legal refusal template with legal aid referral
- [ ] 1.4 Write therapy refusal template with counselor referral
- [ ] 1.5 Review templates for tone and clarity

## 2. Configuration
- [ ] 2.1 Create `config/refusal_templates.json`
- [ ] 2.2 Structure: category, empathy_statement, explanation, resource_links[]
- [ ] 2.3 Include resource titles, URLs, and descriptions
- [ ] 2.4 Add optional phone numbers for crisis resources

## 3. Backend Integration
- [ ] 3.1 Update `get_refusal_template()` to load from config
- [ ] 3.2 Format template with variables (parent name, topic)
- [ ] 3.3 Return structured response with empathy + resources
- [ ] 3.4 Log refusal events for analysis

## 4. Frontend UI Component
- [ ] 4.1 Create `RefusalMessage.tsx` component
- [ ] 4.2 Display empathy statement prominently
- [ ] 4.3 Show explanation in supportive tone
- [ ] 4.4 Render resource links as clickable buttons/cards
- [ ] 4.5 Use distinct styling (warm colors, gentle icons)
- [ ] 4.6 Add accessibility (ARIA labels, keyboard nav)

## 5. Integration
- [ ] 5.1 Detect refusal message type in chat page
- [ ] 5.2 Render RefusalMessage component instead of normal message
- [ ] 5.3 Ensure refusals appear in message flow naturally
- [ ] 5.4 Test all refusal categories render correctly

## 6. Testing
- [ ] 6.1 Unit test each refusal template loads correctly
- [ ] 6.2 Assert empathy statement present in all
- [ ] 6.3 Assert at least one resource link in all
- [ ] 6.4 Visual review of UI rendering
- [ ] 6.5 User feedback on template tone

