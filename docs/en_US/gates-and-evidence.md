# Gates and Evidence

The most common way multi-agent collaboration falls apart: **an agent says "done", but nobody knows whether it's actually true.**

There is only one cure: **put a gate at every stage, require evidence at every gate, and have a non-producer rerun the key evidence.**

## What is a gate

A gate is a checkpoint that can clearly answer "pass / fail". In the software-development Starter these are G0–G4:

| Gate | Content | Who judges |
| --- | --- | --- |
| G0 | Requirements ready: goal + testable acceptance criteria | Leader / Human |
| G1 | Design approved: design aligns with acceptance criteria + acceptable from a business standpoint | Leader (multica-verification skill) + Reviewer (default software-development does business review at G1 only; the reviewed variant gives every artifact a dedicated Reviewer) |
| G2.5 | CI/CD deploy: after G2 PASS and code push, build & deploy to the test env and return the env URL | Leader (checks CI evidence, triggered by @DevOps) |
| G3 | Tests pass: the T3 automation report maps every acceptance criterion (depends on the G2.5 deploy env) | Leader (reviews the report) |
| G4 | Human acceptance: delivery decision | Human |

The key property of a gate is **decidability**: every gate maps to a question that can be answered PASS / FAIL. If you can't judge it, it's not a gate — it's a wish.

## The gatekeeping action: the multica-verification skill

Verification is a **function**, not a role. It is standardized as `templates/en_US/skills/leader/multica-verification/` and triggered by the **Leader** at the gate points (G1 / G2 / G3):

- The Leader produces no artifacts → the gatekeeper and the gated are different parties
- Gatekeeping = rerun the verification commands + map each acceptance criterion item by item, without citing the producer's description; when the repo has CI configured, **prefer the CI verdict** (e.g. `[G2 PASS · CI #123]`) and don't rerun (how to read CI: the `multica-artifact-cicd-sync` skill)
- Producer self-certification (running it yourself) doesn't count; key commands must be rerun

## Verification and review are two different kinds of checks

| | Verification | Review |
| --- | --- | --- |
| Question asked | Is the artifact acceptable? Is there evidence? | Is the design / change acceptable from a business standpoint? |
| How it's judged | Objectively decidable: command output, item-by-item mapping | Subjective judgment: business intent, risk, maintainability |
| Who runs it | Leader (multica-verification skill) / CI | Reviewer (independent role) / Human |

Verification can be standardized into a Skill and machine-run; review must be done by an independent person with a business perspective.

## Two-layer gate: generic gate + professional artifact review

`software-development` has only **one generic gate** (the Leader reruns with the multica-verification skill at G1/G2/G3). `software-development-reviewed` stacks a **second layer: professional artifact review**, forming "generic gate + professional review". They differ in standard, trigger, and are mutually non-substitutable.

### Why two layers

The generic gate answers "**is it correct?**" — does the artifact meet acceptance criteria, is the process complete. That's process-layer assurance; it doesn't judge professional depth. But that's not enough alone: a frontend implementation that "meets AC" may have only无效 unit tests; a test report that "passes acceptance" may cover low-risk paths while missing a critical branch. These **professional-quality issues** need an independent reviewer in the relevant domain.

The professional artifact review answers "**is it professional?**" — a professional analysis of the artifact itself (is the design sound, are unit tests sufficient, are cases/coverage adequate) against requirements, upstream artifacts, and references.

### How the two layers run (fixed order)

```text
Producing role finishes artifact
  → Layer 1 Generic gate (Leader-triggered): multica-verification skill re-checks acceptance/process (only "correct?")
  → if PASS:
      Layer 2 Professional review (dedicated Reviewer-triggered): multica-review-* skill for professional analysis (only "professional?")
        → if PASS: artifact released, advance to next stage
        → if FAIL: dedicated Reviewer outputs conclusion + fix list, reports to Leader
             → Leader dispatches the producing role to fix
             → after fix, re-review by same dedicated Reviewer (same person, consistent口径)
             → max 3 rounds; still FAIL at round 3 → escalate to human
  → if FAIL: return to author, counted as generic-gate FAIL (3 consecutive → escalate to human)
```

Either layer FAIL returns; professional-review rounds and generic-gate FAIL rounds are **counted independently but share the "3-strike cap"** — either layer hitting 3 unresolved strikes escalates to human.

### Role → dedicated Reviewer mapping (reviewed variant)

| Producing role | Dedicated Reviewer | Review skill | Review focus |
| --- | --- | --- | --- |
| @ProductManager (PRD) | @ProductReviewer | multica-review-product | scope/goal/acceptance clear & testable, no missing critical constraints |
| @Architect (design) | @ArchReviewer | multica-review-architect | soundness, extensibility, acceptance alignment, tech risk |
| @Designer (UI) | @DesignReviewer | multica-review-designer | interaction soundness, accessibility, design-system/acceptance consistency |
| @FrontendDev (frontend) | @FrontendReviewer | multica-review-frontend | fit to UI/API contract, component quality, unit tests reasonable & sufficient |
| @BackendDev (backend + API contract) | @BackendReviewer | multica-review-backend | contract quality, design fit, error handling, unit tests reasonable & sufficient |
| @Tester (cases / report) | @TestReviewer | multica-review-test | coverage depth, coverage doc reasonableness, line-by-line acceptance mapping |

> Leader and DevOps get **no** dedicated Reviewer: Leader is orchestrator (gate + review would be同源); DevOps artifact is a deploy URL already covered by CI hard gate. All other regular producing roles are covered.

### Three hard constraints (same as single-layer, stricter)

1. **Dedicated Reviewer doesn't modify on the author's behalf**: only outputs conclusion + fix list and reports to the Leader; the Leader dispatches the producing role to fix. This separates "review power" from "modify power", and advancement stays with the Leader.
2. **Leader must not substitute review conclusion for the generic gate**: each layer owns its own — the generic gate is always run by the Leader personally via multica-verification skill; never skip the rerun just because the dedicated Reviewer said PASS.
3. **Dedicated Reviewer and producer are independent**: the same artifact's re-review must be by the same dedicated Reviewer, keeping review口径 continuous; never let the producer review themselves, nor let the Leader both gatekeep and do professional review.

### When to use the reviewed variant

- You need more than "the process completed" — you need artifacts that are themselves professional and defensible.
- The team holds a high professional bar for architecture design, UI, requirements, frontend/backend implementation, and test artifacts.
- You want professional review opinions **independent of the implementer**, unified and dispatched by the Leader in a fix-and-re-review loop.

If you only want the lightweight flow, use the default `software-development` (just the Leader-triggered multica-verification generic gate). Both Starters are identical in routing / stage-gates / evidence / failure handling / escalation except for the extra review layer — zero migration cost.

## What counts as evidence

"Done" has no evidentiary value. Valuable evidence:

- List of changed files (git diff summary)
- Commands actually executed + full output
- Item-by-item mapping to acceptance criteria (each criterion → the test or check covering it)
- Test / check results
- Known limitations and risks

## How to prevent "author self-certification"

The rule is simple: **don't let the person who did the work judge whether the work is acceptable.**

- Implementers don't pass themselves
- Gatekeeping is done by the Leader rerunning the multica-verification skill (or citing the CI verdict), not by citing the implementer's description
- The gatekeeper personally reruns the automated verification output

## Soft gates (agent world) vs. hard gates (CI)

LLM instructions are guidance, not a safety boundary. **Rules that must be obeyed live outside the LLM:**

```text
Tests / Lint / Build / CI / branch protection / PR approval
```

- **Soft gate**: the Leader gatekeeps inside the Squad with the multica-verification skill (G1–G3), constrained by instructions and evidence — good for getting started, no CI, or an exploration phase.
- **Hard gate**: unforgeable checks produced by CI (deployment templates and practices live in the `multica-artifact-cicd-sync` skill: `templates/en_US/skills/devops/multica-artifact-cicd-sync/`). When you need results more trustworthy than manual checks, hand the critical gates to CI — the gate issuer must be a different party from the gated.

Soft and hard gates are **two execution environments of the same verification function**: the Skill in the agent world and CI in the engineering world. If it can run in CI, run it in CI.

Don't rely on "the agent was asked not to do this."

## A full walkthrough of a real requirement

Using "add a CSV export feature" as an example:

1. **G0**: The Issue states acceptance criteria, e.g. "after calling the export API, the returned CSV contains all filtered results."
2. **G1**: Architect gives a minimal-change plan (reuse the existing export middleware). The Leader uses the multica-verification skill to confirm the plan covers the acceptance criteria, and the Reviewer checks business acceptability.
3. **Implementation**: Frontend / BackendDev (per the Issue scope) submit code + unit tests + changed-file list + verification command output (self-claimed).
4. **G2**: The Leader prefers the CI verdict (or reruns the verification commands if there's no CI) and checks that the diff only touches this requirement. PASS.
5. **G2.5**: @DevOps, after G2 PASS and code pushed, triggers CI/CD, builds & deploys to the test env and returns the env URL; the Leader gates G2.5 PASS from the CI evidence. (Skip when no @DevOps / no triggerable CI; T3 degrades to local/manual verification with explicit labeling.)
6. **G3**: The Tester produces and executes feature / API cases per the multica-test-t1-design skill; after G2.5, runs automation via multica-test-t3-ui-automation against the deploy env, verifies "filter → export → inspect CSV content" against the acceptance criteria, and produces a test report; the Leader reviews whether the report covers every criterion.
7. **G4**: A human reviews the evidence and decides whether to merge / ship.

If any G2/G3 FAILs, the task returns to the responsible implementer and **previous gate conclusions are void — they must be rerun.** "It passed last time" doesn't excuse skipping the rerun. More generally: **once any artifact is modified, its downstream gates become invalid immediately and must be re-judged.** It's not just implementation changes: once design / API contract / cases change, the downstream implementation, testing, and acceptance gates also become invalid — never carry over an old PASS. And when an in-scope artifact is judged "Not Applicable (N/A)", never skip it silently — mark N/A explicitly with the reason and the Leader's confirmation; an unconfirmed N/A counts as a missing scope and is written back to the Issue.

### Gate verdict values

A gate verdict isn't just PASS / FAIL; use these four values:

- **APPROVED**: the artifact stands; open the downstream.
- **APPROVED_NA (not applicable but passed)**: the artifact is confirmed out of scope (e.g. design when "no design"), the branch is treated as passed, **no artifact is produced**, and the downstream follows the "no such artifact" branch. Note its downstream differs from a normal APPROVED — the Leader must state that difference in the routing map; don't conflate the two.
- **REJECTED**: return to the original author with the blocking issue, locating evidence, owner, and verifiable pass condition; never vague notes like "keep optimizing".
- **BLOCKED**: waiting on missing info / dependency; not a pass; never pass it via "environment issue".

### Join gates (parallel branches)

When multiple artifacts advance in parallel and join at one gate (e.g. software-dev G2 = API contract + feature cases, G3 = frontend + backend + API cases), that gate requires **every branch APPROVED to open the downstream**; if any branch is REJECTED, only that branch is returned and the join stays closed. The gatekeeper judges each branch independently and doesn't vouch for a failed branch.

### "AI-readable" discipline for requirement / design artifacts

Requirements and product docs are not only for human review — downstream @Architect / @Designer / @FrontendDev / @BackendDev / @Tester use them to break down tasks. When the Leader gates G0/G1, beyond the four values, also check these hard constraints (from the Product Manager role):

1. **Stable headings**: heading levels and section names in a doc are fixed, so AI can locate (e.g. "Acceptance Criteria" is always AC-, not "acceptance" today and "pass criteria" tomorrow).
2. **Stable table columns**: field tables / metric definitions use fixed column names (e.g. "field / type / required / note").
3. **Numbered rules**: business rules, acceptance criteria, and goals always use G- / FR- / BR- / AC- / KPI- / OP- / RISK- numbering; no unnumbered prose demands.
4. **Centralized open questions**: all uncertainty goes only into the OP- list, not scattered in the body pretending to be confirmed; OP- must be closed before development.
5. **Cross-linked docs**: PRD / prototype notes / metric definitions / acceptance checklist link to each other; don't rely on "that table earlier".
6. **Conflict source-of-truth**: on conflicting sources, state "which doc is authoritative"; don't leave two contradictory docs unarbitrated.
7. **Ban vague words**: no "etc. / relevant / appropriate / optimize a bit" that can't be built or accepted; requirements must be testable.
8. **Rules as text**: important rules must exist as text, not only in images / prototypes (images supplement, never the sole source).

> Violating any point → G0/G1 verdict REJECTED, naming which point is missing; don't silently pass.

### The gatekeeper doesn't edit the artifact

The gatekeeper (the Leader rerunning with multica-verification, or an independent Reviewer) only outputs a verdict and a fix list — **never edits the reviewed artifact on the author's behalf**; the orchestrator also never approves on the reviewer's behalf. This makes the "authors don't self-review" hard constraint hold at the process level.
