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

