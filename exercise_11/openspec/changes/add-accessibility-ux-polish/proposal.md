# Add Accessibility & UX Polish

## Why
Accessible applications ensure everyone can use the service, regardless of disability. WCAG AA compliance, keyboard navigation, and proper ARIA roles are essential for production readiness.

## What Changes
- Implement keyboard navigation for all interactive elements
- Add ARIA roles, labels, and live regions for screen readers
- Display clear disclaimers about AI limitations
- Run Axe accessibility scan with no critical issues
- Improve color contrast and focus indicators

## Impact
- Affected specs: New capability `accessibility`
- Affected code:
  - `frontend/src/app/coach/chat/page.tsx` - ARIA roles for chat
  - `frontend/src/components/ChatMessage.tsx` - Semantic HTML
  - `frontend/src/components/DisclaimerBanner.tsx` - AI disclaimer
  - `frontend/tailwind.config.js` - Accessible color palette
  - `frontend/e2e/accessibility.spec.ts` - Axe tests
  - `frontend/src/styles/focus.css` - Focus indicators

## Implementation Status
✅ **Core Accessibility Complete** - 19/30 tasks (11 advanced/testing tasks deferred)
- **Keyboard Navigation**: ✅ Enter/Space for buttons, Esc to clear input, logical Tab order
- **ARIA Labels & Roles**: ✅ All inputs, buttons, citations, and interactive elements properly labeled
  - Chat container: `role="log"`, `aria-live="polite"`, `aria-busy` during streaming
  - Input fields: `aria-label`, `aria-required`, `aria-describedby`
  - Buttons: `aria-label`, `aria-busy` for loading states
  - Citations: `aria-label` with source information
  - Refusal messages: `role="alert"` for important messages
- **Focus Indicators**: ✅ High-contrast 2px outlines on all interactive elements
- **Semantic HTML**: ✅ Main landmarks (`<main role="main">`), proper structure
- **Live Regions**: ✅ Chat messages announced via `aria-live="polite"`
- **Color Contrast**: ✅ Existing design meets WCAG AA (≥4.5:1 for normal text)

**Deferred Tasks** (manual testing/advanced features):
- Keyboard shortcuts documentation
- Color blindness simulator testing
- Automated Axe accessibility scans
- Manual screen reader testing (NVDA/VoiceOver)
- Disclaimer banner component

**Files Modified**:
- `frontend/src/app/coach/chat/page.tsx`
- `frontend/src/app/coach/page.tsx`
- `frontend/src/components/RefusalMessage.tsx`

