---
name: multica-review-test
description: Test-artifact dedicated review framework. Called by TestReviewer to professionally analyze Tester's cases/report/coverage doc (coverage depth/acceptance mapping/coverage reasonableness/conclusion truth/contract consistency), output PASS/FAIL + fix list, report to Leader.
---

# Test Artifact Professional Review (TestReviewer)

Structured professional review framework for **test artifacts (functional/API cases, test report, coverage doc)**. Called by `TestReviewer`; reviews the links `Tester` returns via `multica-test-orchestration` (case set / report), plus acceptance + related implementation change links Leader passes.

## When to use
- TestReviewer receives a "review test artifact" dispatch from Leader (case review / report review both apply).
- Entering a re-review round after test-artifact changes (check previous round's fix list item by item).

## Review dimensions (conclusion per item)
1. **Coverage depth**: normal / boundary / exception / permission / compatibility paths covered.
2. **Acceptance mapping**: every AC- backed by an executable case.
3. **Coverage reasonableness**: metrics truly reflect risk points, no hiding critical uncovered paths.
4. **Conclusion truth**: pass/fail based on real execution evidence, defects reproducible.
5. **Contract consistency**: case params, assertions aligned with BackendDev contract.

## Output format
```
【Test Artifact Review】<test link>
Conclusion: PASS / FAIL
Blocking items (required on FAIL, each: rationale / involved point / fix direction):
- ...
Suggestions (non-blocking):
- ...
Previous fix-list check (re-review): resolved X / unresolved Y
Round: N / 3
```
Conclusion + fix list **reported to Leader**; don't modify cases or notify Tester yourself.

## Boundaries
- Review only test artifacts, not architecture, requirements, UI, frontend/backend implementation, or code unit tests.
- Don't replace Leader's generic gate (multica-verification skill).
- Implementation-layer quality goes to the matching dedicated Reviewer; you own test-artifact professionalism.
- Still FAIL at round 3 → mark "escalate to human", hand to Leader, stop looping.
