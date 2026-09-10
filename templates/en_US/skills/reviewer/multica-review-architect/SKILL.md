---
name: multica-review-architect
description: Architecture-design dedicated review framework. Called by ArchReviewer to professionally analyze Architect's technical design (soundness/extensibility/acceptance alignment/tech risk), output PASS/FAIL + fix list, report to Leader.
---

# Architecture Design Professional Review (ArchReviewer)

Structured professional review framework for **technical architecture design artifacts**. Called by `ArchReviewer`; reviews the design link `Architect` returns via `multica-artifact-design-sync`.

## When to use
- ArchReviewer receives a "review architecture design" dispatch from Leader.
- Entering a re-review round after design changes (check previous round's fix list item by item).

## Review dimensions (conclusion per item)
1. **Soundness**: layering, module boundaries, dependency direction clear; no over/under-design.
2. **Extensibility & maintainability**: cost of common future changes; obvious tech debt.
3. **Acceptance alignment**: line-by-line coverage of AC-/FR-/BR-; list gaps.
4. **Key technical risk**: performance, consistency, security, data boundaries identified with mitigations; unmitigated risk = blocking.
5. **Cross-end consistency**: contract boundaries with frontend/backend self-consistent, no conflict with UI/API artifacts.

## Output format
```
【Architecture Review】<design link>
Conclusion: PASS / FAIL
Blocking items (required on FAIL, each: rationale / involved point / fix direction):
- ...
Suggestions (non-blocking):
- ...
Previous fix-list check (re-review): resolved X / unresolved Y
Round: N / 3
```
Conclusion + fix list **reported to Leader**; don't modify design or notify Architect yourself.

## Boundaries
- Review only architecture design, not UI, requirements, code, or test cases.
- Don't replace Leader's generic gate (multica-verification skill).
- Still FAIL at round 3 → mark "escalate to human", hand to Leader, stop looping.
