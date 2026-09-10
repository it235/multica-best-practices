---
name: multica-backend-impl
description: Backend implementation skill—API / data model / business logic coding conventions and acceptance checklist; the preferred mount for @BackendDev.
version: 1.0.0
metadata:
  upstream:
    - multica-artifact-architect
  downstream:
    - multica-artifact-backend
    - multica-artifact-cicd-sync
---

# Backend Implementation (backend-impl)

## Responsibility
As @BackendDev, implement backend code (API / data model / business logic) per the architect's technical design, then push the contract to `backend-artifact` via `multica-artifact-backend`.

## Conventions
- Follow the module/package layout agreed in `multica-artifact-architect`.
- API contracts (path/params/response) must match the design exactly.
- Business logic must cover the AC-derived edge cases.

## Acceptance checklist
- [ ] API contract matches design (no silent field changes)
- [ ] Data model migration is reversible
- [ ] Error codes/responses are documented
- [ ] Unit tests cover core logic

## Flow
1. Implement per design.
2. Self-check against the checklist.
3. Push contract to `backend-artifact` (`multica-artifact-backend`), then hand off to @Tester (API automation) and @Reviewer.
