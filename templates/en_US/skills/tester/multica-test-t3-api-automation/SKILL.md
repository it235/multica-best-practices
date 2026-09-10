---
name: multica-test-t3-api-automation
description: T3 API automation—only after G2.5 PASS; run Apifox scenarios by contract, join overall verdict with UI side. Requires env + Apifox three IDs complete; no local mock as substitute.
version: 1.1.0
metadata:
  orchestrates:
    - multica-platform-apifox
    - multica-test-orchestration
---

# API Automation (T3 · API)

T3 only after **G2.5 PASS**; an AC can only be verified by API → run this skill alone; if it also has a UI channel → run both, orchestration merges one report.

> Integrated from `api-automation-squad`. **Material assembly + BLOCKED see `multica-test-orchestration`.**

## Required Items (stop + interruption list if missing; summary from comments)

| Required | How it counts as complete |
| --- | --- |
| G2.5 PASS | Leader/DevOps explicit G2.5 PASS (or "G2.5 N/A" but deploy_url + Leader written authorization) |
| deploy_url | Reachable environment URL |
| contract | Apifox/OAS link, or **N/A (reuse xxx)** |
| Apifox three IDs | project_id / environment_id / scenario_ids **complete**, else **N/A (not missing)** |

## Flow

```bash
python multica-platform-apifox/scripts/run_scenarios.py \
  --project-id <id> --environment-id <id> --scenario-ids <ids> \
  --deploy-url <deploy_url> --out ./reports/apifox.json
```

Scenario source: T2 manifest (MULTICA.md §2 API manifest) or T1 Apifox branch. Missing → interruption list.

## Output and merge

```markdown
# T3 API Automation — {JIRA_KEY}
- G2.5: PASS @ {sha}  deploy: {url}
- Apifox: project {id} env {id} scenarios {ids}
- total / pass / fail / error
- per scenario: id / name / status / latency / assertion / log path
- conclusion: PASS | FAIL | BLOCKED
```

`multica-test-orchestration` merges with UI side: **one side only** verifies a given AC, missing that side → **whole ticket cannot be PASS**; errors → triage (`references/t3-failure-triage.md`).

## Platform Collaboration

| Platform skill | Used for |
| --- | --- |
| `multica-platform-apifox` | Scenario run; results/logs into report |
| `multica-test-orchestration` | T3 gate + merge |

**No local mock** as a substitute for the deployed environment; no environment → BLOCKED.

## Why it works

API verification is independent of UI; running after G2.5 ensures automated evidence is trustworthy; three IDs explicit avoids "silent skip".
