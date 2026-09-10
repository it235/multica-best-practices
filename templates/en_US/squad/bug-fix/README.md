# Bug Fix Starter

> The minimal squad combination: **bug fixes don't go through the Architect.**
> Reuses the Agents under [`../../agents/`](../../agents/) (Leader / FrontendDev / BackendDev / Tester / Reviewer); only the orchestration changes.

## Flow

```text
Bug Issue
  ↓ Determine the impact area (frontend? backend?)
  ↓
FrontendDev / BackendDev (per impact area)
  Reproduce → root cause → fix + regression test
  ↓
Leader (multica-verification skill)
  Independent rerun verification
  ├─ FAIL → back to the responsible implementer
  └─ PASS ↓
  ↓
Reviewer (business review, when necessary)
  ↓
Human
  Acceptance → Done
```

## Stage responsibilities

| Stage | Owner | Deliverable | Checked by |
| --- | --- | --- | --- |
| Reproduce | Frontend / BackendDev | Reproducible steps + root cause | — |
| Fix | Frontend / BackendDev | Minimal-scope fix + regression test | — |
| Verify | Leader | Independent rerun verdict (PASS / FAIL) | Leader (multica-verification skill) |
| Review | Reviewer | Business-risk judgment (when necessary) | Reviewer |
| Accept | Human | Ship / Done decision | Human |

## Differences from software-development

| Stage | Software Development | Bug Fix |
| --- | --- | --- |
| Design | Architect designs first | Skipped; reproduce + locate the root cause first |
| Implementation | Frontend / BackendDev (per scope) | Frontend / BackendDev (per impact area) |
| Gatekeeping | Leader with the multica-verification skill (G1–G3) | Leader reruns the fix verification with the multica-verification skill |
| Testing | Tester full acceptance | Targeted regression tests |
| Acceptance | Human | Human |

## Why there's no Architect

A bug's goal is "restore correct behavior," not "introduce a new capability." An extra design role only slows the fix down and adds context overhead.

This is exactly the repo's core principle:

> **Best practices aren't a fixed five-Agent flow; they're the smallest Agent combination for each task type.**

## Setup

1. Create the Agents per [`../../agents/`](../../agents/): Leader / FrontendDev / BackendDev / Tester / Reviewer.
2. Copy the shared gatekeeping Skill: [`../../skills/leader/multica-verification/SKILL.md`](../../skills/leader/multica-verification/SKILL.md), mounted to the **Leader** (this Starter depends on this one Skill only).
3. Copy [`squad.md`](./squad.md) from this directory into the Squad Instructions (overrides the default orchestration).
4. Create the Bug Issue with [`issue.md`](./issue.md).
5. Assign it to the Squad.

## Important reminder

Fix tasks are especially prone to "skipping verification to ship fast." CI, regression tests, and human approval must stay in the engineering system — don't rely on agent self-discipline.

## When to use

- Urgent production incident fixes
- Feature behavior doesn't match expectations
- Regression issues

## When not to use

- New feature development (use software-development)
- Large architecture migrations
