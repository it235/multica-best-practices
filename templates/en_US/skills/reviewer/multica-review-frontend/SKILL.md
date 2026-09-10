---
name: multica-review-frontend
description: Frontend-implementation dedicated review framework. Called by FrontendReviewer to professionally analyze FrontendDev's output (UI/API-contract fit/component quality/unit-test sufficiency/acceptance mapping), output PASS/FAIL + fix list, report to Leader.
---

# Frontend Implementation Professional Review (FrontendReviewer)

Structured professional review framework for **frontend implementation artifacts**. Called by `FrontendReviewer`; reviews the changed-file list / repo ref `FrontendDev` returns via code-class skill, plus the UI link + API contract link Leader passes.

## When to use
- FrontendReviewer receives a "review frontend implementation" dispatch from Leader.
- Entering a re-review round after implementation changes (check previous round's fix list item by item).

## Review dimensions (conclusion per item)
1. **UI fit**: layout, interaction, states, edge states aligned with Designer output.
2. **API-contract fit**: call params, response handling, error branches aligned with BackendDev contract.
3. **Component quality**: reusability, single responsibility, no obvious smells.
4. **Unit-test sufficiency**: key paths, boundaries, async/error branches covered; no无效的 tests padded for coverage (mark & block).
5. **Acceptance mapping**: implementation truly satisfies every AC-.

## Output format
```
【Frontend Review】<change link>
Conclusion: PASS / FAIL
Blocking items (required on FAIL, each: rationale / involved point / fix direction):
- ...
Suggestions (non-blocking):
- ...
Previous fix-list check (re-review): resolved X / unresolved Y
Round: N / 3
```
Conclusion + fix list **reported to Leader**; don't modify code or notify FrontendDev yourself.

## Boundaries
- Review only frontend implementation & unit tests, not architecture, requirements, UI design, backend, or test cases.
- Don't replace Leader's generic gate (multica-verification skill).
- Still FAIL at round 3 → mark "escalate to human", hand to Leader, stop looping.
