---
name: multica-frontend-impl
description: Frontend implementation skill—page/component/state/style coding conventions and acceptance checklist; the preferred mount for @FrontendDev.
version: 1.0.0
metadata:
  upstream:
    - multica-design-ui-impl
  downstream:
    - multica-artifact-frontend
    - multica-verification
---

# Frontend Implementation (frontend-impl)

## Responsibility
As @FrontendDev, implement pages/components/state/style per the designer's `multica-design-ui-impl` output, then push the deliverable set to `frontend-artifact` via `multica-artifact-frontend`.

## Conventions
- Component/state management follows the project's agreed stack.
- UI must match the design's states (normal/empty/error/loading).
- Reusable components go through the design system.

## Acceptance checklist
- [ ] Pages implement all design states
- [ ] Responsive/layout matches design
- [ ] No hardcoded credentials/URLs
- [ ] run-url reachable after build

## Flow
1. Read upstream design links from `multica-design-ui-impl`.
2. Implement pages/components.
3. Self-check against the checklist.
4. Push to `frontend-artifact` (`multica-artifact-frontend`), then hand off to @Reviewer (G1) and @Tester (T1/T2/T3).
