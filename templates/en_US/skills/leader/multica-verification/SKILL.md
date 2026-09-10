---
name: multica-verification
description: Gatekeeping function: objectively check whether an artifact satisfies the acceptance criteria. Triggered by the Leader to rerun at gate points (G1/G2/G3); members can also use it for self-check. Used for design review / implementation acceptance / test-report review.
---

# Verification (gatekeeping)

## What this is

Verification is a **function**, not a role. It answers one question:

> For every acceptance criterion, is there objective evidence that it is satisfied?

The key: verification must be an **objectively decidable action** (run commands, read output, map item by item), not "I feel it's fine."
It doesn't rely on anyone's character — it relies on the evidence itself. Whoever runs it, the result is the same.

## Who executes it

- **Gatekeeping**: the **Leader** triggers this Skill at the gate points (G1 / G2 / G3) and reruns independently. The Leader produces no artifacts, so it's naturally a third party.
- **Self-check**: after finishing, a producer may first run this Skill to self-verify (pasting the command output), but self-check is not gatekeeping — gatekeeping must be rerun by a non-producer.

> The gate issuer must be a different party from the gated. Authors cannot stamp "PASS" on themselves.

## Process

1. Read the Issue's acceptance criteria.
2. Map every criterion to evidence (which test / which command / which output).
3. **Rerun** the verification commands; don't cite someone else's described output.
4. Check the change scope: does the diff only touch this requirement?
5. Give PASS / FAIL for each criterion.

## Result

**PASS** — every criterion has sufficient evidence.

**FAIL** — at least one criterion unmet. Must provide: the problem, why it matters, where, and the fix direction.

**BLOCKED** — missing information / environment, cannot verify. Report honestly; never turn it into PASS.

## Relationship to CI hard gates

This Skill is the verification function's form in the agent world (soft gate), suitable for getting started, no CI, or an exploration phase.
The same function's machine form is the CI hard-gate template carried by the `multica-gate-setup` skill. If it can run in CI, run it in CI; the soft gate is transitional.

## Why this works

"Verification" is the easiest thing to turn into a formality. Writing verification as a rerunnable action checklist and requiring a non-producer to execute it blocks two kinds of cheating at once: producers pretending they verified (the self-check loophole) and producers stamping themselves PASS (the gatekeeping loophole).
