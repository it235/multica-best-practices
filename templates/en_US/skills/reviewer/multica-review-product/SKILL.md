---
name: multica-review-product
description: Requirements/PRD dedicated review framework. Called by ProductReviewer to professionally analyze ProductManager's PRD (scope clear/goal explicit/acceptance testable/constraints complete/open items), output PASS/FAIL + fix list, report to Leader.
---

# Requirements (PRD) Professional Review (ProductReviewer)

Structured professional review framework for **PRD / requirement artifacts**. Called by `ProductReviewer`; reviews the PRD link `ProductManager` returns via `multica-artifact-req-sync`.

## When to use
- ProductReviewer receives a "review PRD" dispatch from Leader.
- Entering a re-review round after PRD changes (check previous round's fix list item by item).

## Review dimensions (conclusion per item)
1. **Scope clear**: boundaries unambiguous, splittable, no implied scope.
2. **Goal explicit**: problem measurable, no vagueness.
3. **Acceptance testable**: every AC- objectively verifiable, no "good experience" vagueness.
4. **Constraints complete**: permissions, exceptions, compliance, dependencies, data口径 listed.
5. **Open items**: OP- fully listed, not blocking downstream dev (blocking OP- = blocking item).

## Output format
```
【PRD Review】<PRD link>
Conclusion: PASS / FAIL
Blocking items (required on FAIL, each: rationale / involved point / fix direction):
- ...
Suggestions (non-blocking):
- ...
Previous fix-list check (re-review): resolved X / unresolved Y
Round: N / 3
```
Conclusion + fix list **reported to Leader**; don't modify PRD or notify ProductManager yourself.

## Boundaries
- Review only PRD/requirements, not design, code, test cases, or UI.
- Don't replace Leader's generic gate (multica-verification skill).
- Technical feasibility goes to ArchReviewer; you own requirement-layer quality.
- Still FAIL at round 3 → mark "escalate to human", hand to Leader, stop looping.
