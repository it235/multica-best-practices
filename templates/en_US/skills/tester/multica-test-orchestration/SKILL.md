---
name: multica-test-orchestration
description: Tester T1/T2/T3 orchestration and gatekeeping—sub-skill routing, assembling materials from Issue comments, and BLOCKED interruption list. Integrates acceptance-verifier-squad; the preferred mount for @Tester.
version: 1.0.0
metadata:
  orchestrates:
    - multica-test-t1-design
    - multica-test-t2-coverage
    - multica-test-t3-ui-automation
    - multica-test-t3-api-automation
    - multica-platform-jira
    - team-knowledge-base (optional)
    - multica-platform-apifox
---

# Test Orchestration (Acceptance Verifier · Orchestration)

You are accountable for whether the requirement is actually implemented. Testing shifts left and is split into **T1 / T2 / T3**. T3 must wait for DevOps **G2.5 PASS** before running automation.

> **This skill belongs to no single T1/T2/T3 phase**—it is the cross-phase orchestration entry: routing, comment assembly, BLOCKED, and T3 merge adjudication. Integrated from `acceptance-verifier-squad`; method details live in the `-t1`/`-t2`/`-t3` sub-skills.

## Platform Collaboration

| Platform skill | Used for |
| --- | --- |
| `multica-platform-jira` | Read all Issue comments before T2/T3 (`get-issue` / equivalent) |
| `team-knowledge-base (optional)` | T1 Step 0 (via `multica-test-t1-design`) |
| `multica-platform-apifox` | T1 parallel scenarios + T3 batch run (via t1-design / t3-api-automation) |

T1 collection (JIRA / Confluence / Figma) goes through `multica-test-t1-design` → platform-jira / confluence / figma. Credentials and CLIs are **only looked up in the platform skill**.

## Sub-skill Routing (must Read before acting)

| Phase | Skill | Output |
| --- | --- | --- |
| Orchestration / gate | This file | Phase card, BLOCKED reason |
| T1 test design | `multica-test-t1-design` | Full Confluence cases + Apifox scenarios + e2e plan |
| T1 QA | `multica-review-test` | Review Confluence; after 👤 passphrase, XMind/JIRA |
| Parallel API scenarios | `multica-platform-apifox` | Supplement scenarios by API contract (AI branch) |
| T2 | `multica-test-t2-coverage` | Confluence delta + Apifox + MULTICA §2 e2e into repo |
| T3 API | `multica-test-t3-api-automation` → `multica-platform-apifox` | Apifox logs + join overall report |
| T3 UI | `multica-test-t3-ui-automation` | pytest+Playwright 1:1 execution |
| T3 adjudication | Orchestration merges both sides' evidence | Single PASS/FAIL/BLOCKED |

Copyable agent instructions: [`references/agent-instructions.md`](references/agent-instructions.md).  
Skill cross-reference: [`references/skill-inventory.md`](references/skill-inventory.md); T3 merge report: [`references/t3-merge-report.md`](references/t3-merge-report.md); **automation assets into repo**: [`references/automation-assets-lifecycle.md`](references/automation-assets-lifecycle.md).

## Task Card (stop if missing)

```text
stage: T1 | T2 | T3 | parallel-api
issue:                  # Multica and/or Jira Key
ac_source:              # Where the numbered AC- original text lives (Issue/PRD)
```

T2 / T3 materials: assemble **only from this Issue's description + all comments (including attachment names)**. If you cannot assemble, **stop**, output the missing list, and wait for a human to complete the comments before continuing. No fabrication; no local mock / URL not present in comments as a substitute.

## Assemble from Comments (mandatory)

Before entering T2 / T3 / parallel-api, you must `jira_cli.py get-issue --comments` (or equivalently read all comments) and fill the task card by recognizing the following:

| Field | Recognized if any of these appears in comments |
| --- | --- |
| `g2_pass` | Leader explicitly writes G2 PASS / G2 convergence gate PASS |
| `g2_sha` / change | Merged SHA, frontend/backend commits, changed-files table, or MR/PR link |
| `api_contract` | Apifox/OAS link, or explicit **N/A + which interface/link is reused** |
| `g25_pass` | Leader/DevOps explicitly **G2.5 PASS**; only "G2.5 N/A" → automation lacks deploy evidence (unless there is also a deploy_url and Leader authorizes in writing) |
| `page_url` | URL of the page under test; if omitted may equal deploy_url (must be stated in comments) |
| `ui_auth` | Only when running UI: `auth_mode=none` or "account via Secret variable name". **Never use plaintext passwords from comments** |
| `apifox_project_id` / `environment_id` / `scenario_ids` | Numeric ID or scenario link; if contract is N/A and this iteration has no API automation → mark all three **N/A (not missing)** |

On conflict: **the later Leader comment wins**. Branch name only, with no SHA/files table/MR link → change item still counts as missing.

### Stop if missing (output to human)

```markdown
## Interrupted: awaiting human to add to Issue comments

Phase: T2 | T3
Issue: {id}

### Already assembled from comments
- {field}: {excerpt source comment summary}

### Missing list (please reply in comments using the right-column format)
| Missing | Please provide |
|--------|--------|
| g2_sha / changed files or MR link | e.g. SHA + file list, or GitLab MR URL |
| api_contract | Apifox/OAS link, or: N/A (reuse xxx) |
| g25_pass | G2.5 PASS or explicitly not passed |
| deploy_url | Reachable environment URL |
| apifox_project_id | Number, or N/A |
| apifox_environment_id | Number or environment name, or N/A |
| apifox_scenario_ids | Scenario ID list, or N/A |

Reply "continue T2" or "continue T3" once completed.
```

## Gates (non-negotiable)

- **Do not pass** merely because it compiles, unit tests pass, or the implementer says it's fine.
- **Do not convert BLOCKED into PASS.**
- **No T3 automation when G2.5 is not PASS**; no local mock as a substitute for the deployed environment.
- **G2.5 N/A**: no deploy_url → T3 automation **BLOCKED**; with deploy_url + Leader written authorization → may run, report notes the downgrade.
- **Manual appendix** (only with Leader written authorization): may list manual results, titled "non-automated, does not replace G2.5"; **must not** therefore pass the whole automation (see `t3-merge-report.md`).
- T1 import: requires `multica-review-test` non-Block, and user/Leader **explicit import passphrase**.
- T2 conclusion only allows "evaluation complete / evaluation BLOCKED", **never** worded as acceptance PASS/FAIL.
- Interface cases are not imported into JIRA.

## T1 Flow

1. Lock Issue + AC- original text.
2. `multica-test-t1-design` — full Confluence **t1-cases** (**no XMind**) + parallel Apifox (once contract ready).
3. `multica-review-test` — review Confluence.
4. After 👤 passphrase: XMind → `import_to_tracker.py` (phase C).
5. Plan e2e / API manifest path (**MULTICA.md §2**; lands in T2).

Leader judges the T1 gate (Confluence link + Apifox summary).

## T2 (only after G2 PASS)

Assemble comment materials → `multica-test-t2-coverage`: Confluence delta + Apifox scenarios + **Playwright writes MULTICA §2 e2e path** + manifest update → commit to deploy branch.

## T3 (only after G2.5 PASS + URL)

First assemble `g25_pass` + `deploy_url`.

| Condition | Action |
| --- | --- |
| Confirmed cases + page_url + **e2e script in deploy branch** (path in MULTICA §2) | `multica-test-t3-ui-automation` |
| Contract not N/A + manifest or Apifox three IDs complete | `multica-test-t3-api-automation` |
| Both complete | Run both, then merge one AC report |
| One side's materials missing | That side interrupted; the other may run. If an AC can only be verified by the missing side → **whole ticket cannot be PASS** |

When there is no UI channel, Apifox materials still follow the contract requirement; when there is no API channel, Apifox three IDs marked N/A **do not count as missing**.

**Never** use `xmind-ui-automation`, `playwright.git`, `req-figma-ui-automation` as T3 UI prerequisites.

Merge report template: [`references/t3-merge-report.md`](references/t3-merge-report.md). **FAIL/ERROR triage**: [`references/t3-failure-triage.md`](references/t3-failure-triage.md) (**@Tester** responsible; fix case problems yourself, assign product problems to FE/BE). Report corresponds to G3.

## Why it works

Orchestration is separated from content skills: Tester only needs to mount this skill to know phase routing and hard gates; sub-skills can evolve independently.
