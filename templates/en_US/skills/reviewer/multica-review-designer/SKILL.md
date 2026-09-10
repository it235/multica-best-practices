---
name: multica-review-designer
description: UI-design dedicated review framework. Called by DesignReviewer to professionally analyze Designer's UI/interaction design (interaction soundness/accessibility/design-system consistency/edge states), output PASS/FAIL + fix list, report to Leader.
---

# UI Design Professional Review (DesignReviewer)

Structured professional review framework for **UI / interaction design artifacts**. Called by `DesignReviewer`; reviews the Figma/design-platform link `Designer` returns via `multica-artifact-ui-sync`.

## When to use
- DesignReviewer receives a "review UI design" dispatch from Leader.
- Entering a re-review round after design changes (check previous round's fix list item by item).

## Review dimensions (conclusion per item)
1. **Interaction soundness**: flow smooth, matches user mental model, no redundant steps.
2. **Accessibility**: contrast, focus management, a11y annotations in place.
3. **Design-system consistency**: components, font, spacing, states aligned.
4. **Edge states**: empty / loading / error / overflow text covered.
5. **Technical feasibility**: no obviously unimplementable or high-cost interactions (mark & hand to Leader).

## Output format
```
【UI Review】<design link>
Conclusion: PASS / FAIL
Blocking items (required on FAIL, each: rationale / involved point / fix direction):
- ...
Suggestions (non-blocking):
- ...
Previous fix-list check (re-review): resolved X / unresolved Y
Round: N / 3
```
Conclusion + fix list **reported to Leader**; don't modify design or notify Designer yourself.

## Boundaries
- Review only UI design, not architecture, requirements, code, or test cases.
- Don't replace Leader's generic gate (multica-verification skill).
- Still FAIL at round 3 → mark "escalate to human", hand to Leader, stop looping.
