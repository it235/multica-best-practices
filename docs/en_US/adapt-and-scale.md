# Cut Down and Scale

> Get it running first, then tune. Don't spend day one "designing the perfect config."

## When to use a Squad, and when to assign directly to an Agent

| Scenario | Approach |
| --- | --- |
| Single-step small task (fix a typo, add one config line) | Assign directly to one Agent, no Squad needed |
| Multi-stage task (design → implement → review → test) | Use a Squad + Starter |
| Urgent production failure | bug-fix Starter |
| Research / technical investigation | See technical-research (below) |

Principle: **if a single Agent can do it, don't add a Squad.** The value of a Squad is cross-stage coordination, not "the more the merrier."

## Start from the smallest combination

Not every task needs 4 Workers. A common growth path:

```text
1 Agent   → assign directly
2 Agents  → Frontend/BackendDev + Reviewer (implementation + independent business review)
3 Agents  → Leader + Frontend/BackendDev + Reviewer (someone gates + reviews)
4 Agents  → Leader + Architect + Frontend/BackendDev + Reviewer (adds a design stage)
5 Agents  → full Starter (+ Tester)
6+ Agents → frontend and backend in the same squad (FrontendDev + BackendDev in parallel)
```

For every Agent you add, ask: **is the new independent judgment point worth the extra context overhead?**

## When you need a stricter process

Escalate to a strict delivery process (stage-by-stage gates, evidence filing, human approval) when:

- Production data / online releases are involved
- Security is involved
- Multi-module, multi-team collaboration
- Domains where correctness can't be verified automatically

Conversely, exploratory / low-risk tasks should use a lightweight process.

## Model adaptation

Different models differ significantly in capability:

- Strong reasoning models: can take on Leader gatekeeping and Reviewer business review roles; gates can be stricter.
- Weaker models: shrink each Agent's task granularity, spell out steps more explicitly, and add human checkpoints when necessary.

Run one real task with the default Starter first, then adjust based on failure modes — don't prepare for "what if" in advance.

## Use AI to adapt the repo to your tech stack

If you don't want to hand-edit templates, copy this straight into Multica or any AI:

```text
You are the adaptation assistant for this repo (multica-best-practices).
Adapt the templates/en_US/squad/software-development template set to my tech stack
([fill in language / framework / toolchain]). Requirements:
1. Replace the verification commands with the real commands of our project (lint / test / build).
2. Keep the G0–G4 gate structure; only change the verification method and examples.
3. Don't add roles or expand the process.
4. Output the complete config that can be pasted directly into Multica.
```

## Pilot and rollout checklist

When rolling out from zero to a team:

1. **Run one real project first**: pick a low-risk Issue with clear boundaries and run the software-development Starter end to end.
2. **Retrospect**: record gate conclusions and failure modes, adjust the templates — don't expand the process right away.
3. **Then roll out**: once stable, introduce other Starters or add Agents.

## FAQ

**Q: The Starter has no PM / QA. Is that enough? What about frontend / backend?**

A: Six roles are enough for ordinary features. The PM role is covered by the Issue template (background / goal / non-goals); the QA role is covered by multica-verification skill gatekeeping + Tester + CI. Frontend / backend are already split into FrontendDev / BackendDev (frontend works with UI design; backend doesn't touch UI), and **routing follows the Issue's "affected ends" scope, so any role can be missing** — no design / no frontend / no backend are all permutations of the same Squad instructions.

**Q: Can I use my own Squad flow?**

A: Yes. The Starter's core value is "responsibility boundaries" and "evidence gates"; the flow itself should adapt to your project. Multi-instance reuse: see [`naming-conventions.md`](./naming-conventions.md) (role + project + member-id).

**Q: Why isn't there a technical-research Starter?**

A: The smallest combination for research tasks is "Researcher → Leader gates (multica-verification skill) → Human." We'll add it once there's a real need, to avoid shipping unvalidated templates (see [`ROADMAP.md`](../../ROADMAP.md)).

## References

- Multica official docs and community practice links: see the "Resources" section at the bottom of [`README.md`](../../README.md)
- Gate implementation: CI hard-gate templates ship inside the `multica-gate-setup` skill ([`templates/en_US/skills/devops/multica-gate-setup/`](../../templates/en_US/skills/devops/multica-gate-setup/))
