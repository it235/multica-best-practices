---
name: multica-gate-setup
description: Integrate CI hard gates into the target repository and make gatekeeping read the CI verdict. Used for deploying gates, reading check-runs for G2, and falling back to soft gates when there's no CI.
---

# Gate Setup (CI gate integration)

## What this is

An integration Skill that upgrades "verification" from agent self-discipline to machine-executed CI.
Core idea (`multica-gatekit`): **the gate issuer must be a different party from the gated** — authors can't stamp "tests passed" on themselves; only CI's actual run results count.

This Skill answers two questions:

1. **How do you install gates into a repository?** (one-time deployment)
2. **How does gatekeeping read the CI verdict?** (G2 on every task)

## Template files it carries

The 3 template files needed for deployment live in the same directory as this SKILL.md (the Skill is self-contained; copy them together with the skill):

| File | Purpose |
| --- | --- |
| `delivery-gate.yml` | CI workflow: runs lint + test + build on PRs and writes a structured gate conclusion |
| `branch-protection.json` | Branch protection rules: require the `delivery-gate` status check to pass + independent approval before merging |
| `apply-branch-protection.sh` | Applies the protection rules to the repo with the `gh` CLI (edit the placeholders, then run) |

Fit: you already have runnable test / lint / build commands; you don't want "Worker self-certifies done" to leave room for cheating; multiple squads in parallel need a unified merge gate.

## Capability prerequisites (route by environment)

The Leader only has the Skill + MCP, no shell. So branch by the runtime environment:

| Capability | Gatekeeping (G2) | Deployment (one-time) |
| --- | --- | --- |
| Has GitHub MCP (read) | **Real integration**: query check-runs to read the CI verdict | — |
| Has GitHub MCP (write) | — | **Real integration**: create the workflow + set branch protection |
| No MCP | **Weak integration**: read the CI verdict humans paste into the PR comment | Human runs the script; you verify the output |

## Deployment flow (one-time)

1. Read the 3 template files in this Skill's directory: `delivery-gate.yml` / `branch-protection.json` / `apply-branch-protection.sh`.
2. Replace the placeholders for the target repository:

| File | Placeholder | Replace with |
| --- | --- | --- |
| `delivery-gate.yml` | `pnpm install --frozen-lockfile` | The repo's real install command |
| | `pnpm lint` / `pnpm test` / `pnpm build` | The repo's real verification commands |
| `branch-protection.json` | `"delivery-gate"` (context) | Keep (unless you renamed the workflow job) |
| | `required_approving_review_count` | Independent approval count (default 1) |
| `apply-branch-protection.sh` | `YOUR_OWNER` | GitHub org / username |
| | `YOUR_REPO` | Repository name |

> This branch-protection API can require an approval count, but it cannot use a team slug to require approval from a specific team. For team-level approval, configure `CODEOWNERS` with required code-owner reviews or use GitHub Rulesets; this template does not create those repository policies automatically.

3. Install into the target repository:
   - **With write-capable MCP**: create `.github/workflows/delivery-gate.yml`; set branch protection with the GitHub API `PUT /repos/{owner}/{repo}/branches/main/protection` (equivalent to the script's action; body from `branch-protection.json`).
   - **Without MCP**: give the human an explicit checklist — copy `delivery-gate.yml` into `.github/workflows/`; edit the placeholders in both files; after `gh auth login` with admin rights, run `bash apply-branch-protection.sh`.
4. Verify it took effect: query the branch protection rules `GET /repos/{owner}/{repo}/branches/main/protection` and confirm `required_status_checks.contexts` contains `delivery-gate`; or have the human paste the script output.

## Gatekeeping flow (G2, every task)

1. Query the PR's check-runs via GitHub MCP: `GET /repos/{owner}/{repo}/commits/{sha}/check-runs`.
2. Find the check named `delivery-gate` (success → PASS, failure → FAIL).
3. G2 verdict:
   - **CI exists** → cite the verdict (e.g. `[G2 PASS · CI #123]`), then check whether the diff only touches this requirement → give PASS / FAIL. **Don't rerun** the commands CI already covered.
   - **CI missing** → fall back to the soft gate: rerun the verification commands with the `multica-verification` skill.
   - **CI unreachable** → BLOCKED, report honestly, never turn it into PASS.
4. When CI exists, the rerun action is "verify the verdict + diff", not rerunning commands.

## Result

**PASS** — CI green (or rerun passed) + diff scope correct.

**FAIL** — CI red or the diff is out of scope. Must provide: the problem, why it matters, where, and the fix direction.

**BLOCKED** — missing MCP / CI / information, cannot verify. Report honestly; never turn it into PASS.

## Relationship to the multica-verification skill

Two execution environments of the same verification function:

- `multica-verification`: soft gate, Leader reruns (this Skill falls back to it when CI is missing)
- `multica-gate-setup`: hard-gate integration — deploy + gatekeeping reads the CI verdict

**If it can run in CI, run it in CI**; the soft gate is transitional. They complement each other; they don't conflict.

## Why this works

If the gate is only "the agent was asked to check," two kinds of cheating remain: authors pretending they verified, and authors stamping themselves PASS. CI makes the issuer a machine (unforgeable), and this Skill encodes that handoff into the flow — a clear deployment checklist, a clear verdict source for gatekeeping, and a clear fallback when there's no CI. No improvisation required.
