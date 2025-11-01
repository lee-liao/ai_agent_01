# Implementation Tasks

## 1. Keyboard Navigation
- [ ] 1.1 Ensure all buttons/links accessible via Tab
- [ ] 1.2 Implement Esc to close modals
- [ ] 1.3 Add Enter/Space to submit messages
- [ ] 1.4 Add keyboard shortcuts documentation
- [ ] 1.5 Test tab order is logical

## 2. ARIA Roles & Labels
- [ ] 2.1 Add `role="log"` and `aria-live="polite"` to chat container
- [ ] 2.2 Add `aria-label` to input field ("Enter your question")
- [ ] 2.3 Add `aria-label` to send button ("Send message")
- [ ] 2.4 Add `aria-busy` during message streaming
- [ ] 2.5 Add `aria-label` to citation badges
- [ ] 2.6 Ensure landmark roles (main, nav, footer)

## 3. Color Contrast
- [ ] 3.1 Audit all text/background color combinations
- [ ] 3.2 Ensure ≥4.5:1 contrast for normal text
- [ ] 3.3 Ensure ≥3:1 contrast for large text
- [ ] 3.4 Update Tailwind colors if needed
- [ ] 3.5 Test with color blindness simulators

## 4. Focus Indicators
- [ ] 4.1 Create `focus.css` with visible focus styles
- [ ] 4.2 Use 2px solid outline with high contrast
- [ ] 4.3 Ensure focus indicators on all interactive elements
- [ ] 4.4 Don't remove focus styles with `outline: none`
- [ ] 4.5 Test focus visibility on all backgrounds

## 5. Disclaimers
- [ ] 5.1 Create `DisclaimerBanner` component
- [ ] 5.2 Display on chat page: "AI-generated advice. Consult professionals for serious concerns."
- [ ] 5.3 Add disclaimer to refusal messages
- [ ] 5.4 Include link to safety policy
- [ ] 5.5 Make dismissible but show on first visit

## 6. Accessibility Testing
- [ ] 6.1 Install @axe-core/playwright
- [ ] 6.2 Create `e2e/accessibility.spec.ts`
- [ ] 6.3 Run Axe scan on all key pages
- [ ] 6.4 Assert no critical or serious violations
- [ ] 6.5 Document any moderate issues for future work

## 7. Screen Reader Testing
- [ ] 7.1 Test with NVDA (Windows) or VoiceOver (Mac)
- [ ] 7.2 Verify chat messages are announced
- [ ] 7.3 Verify form labels are read correctly
- [ ] 7.4 Verify navigation is clear
- [ ] 7.5 Document any issues found

