# Implementation Tasks

## 1. Refusal Template Content
- [x] 1.1 Write empathetic medical refusal template with pediatrician referral
- [x] 1.2 Write crisis refusal template with hotline numbers (988, local resources)
- [x] 1.3 Write legal refusal template with legal aid referral
- [x] 1.4 Write therapy refusal template with counselor referral
- [x] 1.5 Review templates for tone and clarity

## 2. Configuration
- [x] 2.1 Create `config/refusal_templates.json` (INLINE in guardrails.py for minimal demo)
- [x] 2.2 Structure: category, empathy_statement, explanation, resource_links[]
- [x] 2.3 Include resource titles, URLs, and descriptions
- [x] 2.4 Add optional phone numbers for crisis resources

## 3. Backend Integration
- [x] 3.1 Update `get_refusal_template()` to load from config (inline templates)
- [x] 3.2 Format template with variables (parent name, topic)
- [x] 3.3 Return structured response with empathy + resources
- [ ] 3.4 Log refusal events for analysis (DEFERRED)

## 4. Frontend UI Component
- [x] 4.1 Create `RefusalMessage.tsx` component
- [x] 4.2 Display empathy statement prominently
- [x] 4.3 Show explanation in supportive tone
- [x] 4.4 Render resource links as clickable buttons/cards
- [x] 4.5 Use distinct styling (warm colors, gentle icons)
- [x] 4.6 Add accessibility (ARIA labels, keyboard nav)

## 5. Integration
- [x] 5.1 Detect refusal message type in chat page
- [x] 5.2 Render RefusalMessage component instead of normal message
- [x] 5.3 Ensure refusals appear in message flow naturally
- [x] 5.4 Test all refusal categories render correctly

## 6. Testing
- [x] 6.1 Unit test each refusal template loads correctly (in test_guardrails.py)
- [x] 6.2 Assert empathy statement present in all
- [x] 6.3 Assert at least one resource link in all
- [x] 6.4 Visual review of UI rendering
- [x] 6.5 User feedback on template tone (manual testing done)

**Status**: ✅ Complete - 27/28 tasks (1 deferred logging)  
**Pass Criteria**: ✅ All refusals show empathy + resource link  
**Commit**: 469516d

