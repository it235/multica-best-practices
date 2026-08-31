# Software Development Starter

> An out-of-the-box Multica squad for regular software feature development.
> **Copy → Paste → Run**, up and running in 5 minutes.

## Team

```text
                Leader
                  │
    ┌─────────────┼─────────────┐
    ↓             ↓             ↓
Architect  FrontendDev  BackendDev
    │             │             │
    └──────┬──────┴──────┬──────┘
           ↓             ↓
        Tester（cases shift left）  ↓
        Reviewer（business review）
```

## Workflow

Trim by the Issue's scope; any role can be missing:

```text
Issue
  ↓ G0 Determine scope (design? frontend? backend?) ── vague scope → write back to Issue / ask Human
  ↓
[Design] Architect ── G1: Leader (multica-verification skill) aligns acceptance criteria + Reviewer business review ── FAIL → back to Architect
  ↓ PASS
[In parallel]
  ├─ [Backend] BackendDev: API contract → Leader gate
  └─ [Testing] Tester: feature cases → Leader gate
  ↓ G1.5: every in-scope branch passes
[Implementation and API cases] (parallel once the API contract is ready)
  ├─ [Frontend] FrontendDev (works with the UI design) → G2: Leader reruns the verification commands
  ├─ [Backend] BackendDev → G2: Leader reruns the verification commands
  └─ [Testing] Tester: API test cases → Leader gate
  ↓ G2: every in-scope branch passes
[Testing] Tester: execute → test report
  ↓ G3: Leader reviews item-by-item coverage of the acceptance criteria ── FAIL → back to the responsible implementer
  ↓ PASS
Human (G4 human acceptance)
  ↓
Done
```

> `[xxx]` = run only if the scope includes that role; missing roles skip their lines and the gate chain stays intact.

## Artifacts and gates

| Artifact | Producer (per scope) | Gate |
| --- | --- | --- |
| Requirements ready | Issue / Human | G0 (scope + goal + acceptance criteria) |
| Design | Architect | G1 (Leader with the multica-verification skill + Reviewer business review) |
| API contract | BackendDev | Leader gate (parallel input for frontend / testing) |
| Feature cases | Tester | Leader gate |
| Development readiness | Leader | G1.5 (all in-scope API-contract / feature-case branches pass) |
| Frontend implementation | FrontendDev | G2 (Leader reruns the verification commands) |
| Backend implementation | BackendDev | G2 (Leader reruns the verification commands) |
| API test cases | Tester | Leader gate |
| Test report | Tester | G3 (Leader reviews item by item) |
| Acceptance | Human | G4 (delivery decision) |

## Single-task execution contract

Every Leader dispatch contains exactly one independently verifiable artifact and states five things: task, versioned inputs, output format, verification and PASS conditions, and change boundaries. Members respond with “Verdict / Artifact or Changes / AC Mapping / Verification Evidence / Risks and Open Questions”; a bare “done” is not a delivery. The Leader owns both the main-flow state and parallel-branch states, and never advances through a join gate until it passes.

## When to use

- New features / small-to-medium changes
- API, backend, frontend development (frontend/backend can be split; routed by the Issue scope)
- Refactoring with clear requirements

## When not to use

- Urgent production incidents → use the [`bug-fix`](../bug-fix/README.md) Starter
- Large architecture migrations
- Highly vague product exploration

## 5-minute setup

### Step 1 — Create the Agents

Create Agents in Multica (decide which ones per your scope; naming follows "role + project + member-id" in [`docs/naming-conventions.md`](../../../../docs/en_US/naming-conventions.md)). Minimum usable set:

```text
Architect
FrontendDev
BackendDev
Tester
Reviewer
```

Add `DevOps` when scope includes CI/CD; `ProductManager` when the Issue doesn't already provide a ready scope. Copy the code block from the matching file under [`../../agents/`](../../agents/) into each Agent's Instructions.

> The Leader doesn't need a separate Agent: `squad.md` is the Leader's behavior config (Multica's Squad Instructions are only injected into the Leader).

### Step 2 — Create the Skills

Create 13 Skills in Multica:

| Skill | Source | Mount to |
| --- | --- | --- |
| `multica-verification` (gatekeeping, required) | [`../../skills/multica-verification/SKILL.md`](../../skills/multica-verification/SKILL.md) | **Leader** |
| `multica-gate-setup` | [`../../skills/multica-gate-setup/SKILL.md`](../../skills/multica-gate-setup/SKILL.md) | Leader (when integrating CI hard gates) |
| `multica-test-design` | [`../../skills/multica-test-design/SKILL.md`](../../skills/multica-test-design/SKILL.md) | Tester |
| `multica-requirement-analysis` | [`../../skills/multica-requirement-analysis/SKILL.md`](../../skills/multica-requirement-analysis/SKILL.md) | Leader / Architect |
| `multica-technical-design` | [`../../skills/multica-technical-design/SKILL.md`](../../skills/multica-technical-design/SKILL.md) | Architect |
| `multica-implementation` | [`../../skills/multica-implementation/SKILL.md`](../../skills/multica-implementation/SKILL.md) | FrontendDev / BackendDev |
| `multica-artifact-req-sync` | [`../../skills/multica-artifact-req-sync/SKILL.md`](../../skills/multica-artifact-req-sync/SKILL.md) | ProductManager |
| `multica-artifact-ui-sync` | [`../../skills/multica-artifact-ui-sync/SKILL.md`](../../skills/multica-artifact-ui-sync/SKILL.md) | Designer |
| `multica-artifact-design-sync` | [`../../skills/multica-artifact-design-sync/SKILL.md`](../../skills/multica-artifact-design-sync/SKILL.md) | Architect |
| `multica-artifact-api-sync` | [`../../skills/multica-artifact-api-sync/SKILL.md`](../../skills/multica-artifact-api-sync/SKILL.md) | BackendDev |
| `multica-artifact-test-sync` | [`../../skills/multica-artifact-test-sync/SKILL.md`](../../skills/multica-artifact-test-sync/SKILL.md) | Tester |
| `multica-artifact-cicd-sync` | [`../../skills/multica-artifact-cicd-sync/SKILL.md`](../../skills/multica-artifact-cicd-sync/SKILL.md) | DevOps |
| `multica-test-automation` | [`../../skills/multica-test-automation/SKILL.md`](../../skills/multica-test-automation/SKILL.md) | Tester (T3) |
> All six `multica-artifact-*-sync` skills use fixed repo-relative paths under `artifacts/<issue-id>/`, with no platform shell, credential, or network dependency.

### Step 3 — Create the Squad

Create a Squad and copy the code block from [`squad.md`](./squad.md) into the Squad Instructions.

### Step 4 — Create the Issue

Copy the template from [`issue.md`](./issue.md) into a new Issue and fill in your requirement.

### Step 5 — Assign

Assign the Issue to this Squad.

### Step 6 — Run

The squad automatically walks the workflow above:

```text
Issue → [Design] → [parallel artifacts] → [Implementation] → [Testing] → Human
```

Every artifact is gated by the Leader with the multica-verification skill; PASS moves it forward. Roles outside the scope are skipped.
That's it. Run one real requirement, then tune it to your team.

## Important reminder

This flow is a **coordination guide, not a hard constraint.** It doesn't replace:

- CI hard gates (see [`../../skills/multica-gate-setup/`](../../skills/multica-gate-setup/))
- Branch protection / PR review
- Human approval

The multica-verification skill is a **soft gate** in the agent world (executed by the Leader). "Must pass" hard constraints belong in the engineering system, enforced by machines — don't rely on "the agent was asked to do so."

## Directory

| File | Purpose |
| --- | --- |
| `squad.md` | Squad Instructions (conditional routing + artifact gates + evidence requirements) |
| `issue.md` | Standard Issue template (trimmed to a requirement contract: source pick-one + background/goal/scope-with-affected-ends/non-goals/acceptance criteria only) |
| `README.md` | This file (workflow + artifact gates + setup steps) |
| [`../../agents/`](../../agents/) | Shared Agent Instructions (architect / frontend-developer / backend-developer / tester / reviewer / leader) |
| [`../../skills/`](../../skills/) | Shared Skills (16, unified multica- prefix: gatekeeping / CI integration / test design / requirement analysis / technical design / implementation / artifact-orchestration / platform-shell) |

## Why this works

This Starter has 9 roles: the Leader owns orchestration and gatekeeping; ProductManager (product requirement / PRD) turns ideas into reviewable deliverables; Architect (technical) / Designer (UI, platform via `multica-artifact-ui-sync`) / FrontendDev / BackendDev / Tester (T1/T2/T3 three-phase) / DevOps (G2.5 triggers CI/CD) each own a piece of the artifacts, and the **Reviewer does the business review**.
Gatekeeping is standardized as [`../../skills/multica-verification/SKILL.md`](../../skills/multica-verification/SKILL.md), executed by the non-producing Leader (executor and gatekeeper are different parties); objective verification that can be machine-run is upgraded to CI hard gates (see [`../../skills/multica-gate-setup/`](../../skills/multica-gate-setup/)).
**Gates anchor to artifacts, not roles**: the Issue's "affected ends" decides routing; artifacts for missing roles are skipped and the gate chain stays intact — no design / no frontend / no backend / full-stack are all permutations of the same instructions.
Routing logic is written once (Squad), not copied into every Agent; each Agent has a narrow responsibility and can be copied as-is.

## Common failure

- Stuffing the full flow into every Agent → redundant and contradictory.
- Letting the producer judge their own "PASS" → authors instinctively make excuses for themselves; it's the same as not checking.
- Starting without acceptance criteria or an "affected ends" scope in the Issue → the squad gets stuck at G0, a wasted run.
