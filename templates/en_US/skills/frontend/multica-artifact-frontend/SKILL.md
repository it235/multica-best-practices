---
name: multica-artifact-frontend
description: Frontend artifact sync—push the frontend deliverable set (page/component/state/style) and run-url to Multica frontend-artifact (product-requirement mapping); the preferred mount for @FrontendDev.
version: 1.0.0
metadata:
  upstream:
    - multica-frontend-impl
    - multica-design-ui-impl
  downstream:
    - multica-verification
    - multica-artifact-cicd-sync
  note: Frontend artifact is the product-requirement mapping surface; keep fields 1:1 with requirement/design.
---

# Frontend Artifact (frontend-artifact)

## Responsibility
As @FrontendDev, after the page is implemented, push the **frontend deliverable set** and **run-url** to Multica `frontend-artifact` (product-requirement mapping surface). This is the input for @Reviewer (G1) and @Tester (T1/T2), and the basis for release/verification.

## Push content (must be complete)
- Page list (route + name + screenshot/link)
- Component/state/style deliverable set
- run-url (reachable after deployment)
- Requirement/design traceability (which AC each page covers)

## Flow
1. Implement pages per `multica-frontend-impl`, consuming upstream `multica-design-ui-impl` design links.
2. Assemble the deliverable set + run-url.
3. Push to Multica `frontend-artifact` (product-requirement mapping): `python scripts/import_to_multica.py --artifact frontend --json frontend-artifact.json` (see `references/import-contract.md`).
4. Hand off to @Reviewer (G1 business review) and @Tester (T1/T2).

## Notes
- Keep fields 1:1 with requirement/design; do not drift.
- run-url must be reachable; otherwise @Tester T3 will be BLOCKED.
- Do not confuse with `backend-artifact` (that is @BackendDev's contract surface).
