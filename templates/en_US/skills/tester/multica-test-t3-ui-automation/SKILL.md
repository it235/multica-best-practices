---
name: multica-test-t3-ui-automation
description: T3 UI automation—only after G2.5 PASS; run pytest+Playwright 1:1 by MULTICA §2 e2e path and T1 cases; join overall verdict with API side. No local mock.
version: 1.2.0
metadata:
  orchestrates:
    - multica-test-orchestration
---

# UI Automation (T3 · UI)

T3 only after **G2.5 PASS**; an AC can only be verified by UI → run this skill alone; if it also has an API channel → run both, orchestration merges one report.

> Integrated from `ui-automation-squad`. **Material assembly + BLOCKED see `multica-test-orchestration`.**

## Required Items (stop + interruption list if missing; summary from comments)

| Required | How it counts as complete |
| --- | --- |
| G2.5 PASS | Leader/DevOps explicit G2.5 PASS (or deploy_url + Leader written authorization) |
| deploy_url | Reachable environment URL |
| page_url | Page URL; if omitted must equal deploy_url (state in comments) |
| e2e script | **Path in MULTICA.md §2**; in deploy branch at G2.5 SHA, **1:1** with cases |
| ui_auth | `auth_mode=none` or "account via Secret variable name"; **never plaintext password from comments** |

**Never** use `xmind-ui-automation` / `playwright.git` / `req-figma-ui-automation` as prerequisites.

## Flow

```bash
pytest <MULTICA.md §2 e2e path> --base-url <page_url> --alluredir ./reports/ui
```

Cases source: T1 Confluence t1-cases + T2 supplement. Missing script path → interruption list.

## Output and merge

```markdown
# T3 UI Automation — {JIRA_KEY}
- G2.5: PASS @ {sha}  deploy: {url}  page: {page_url}
- e2e: {MULTICA.md §2 path}
- total / pass / fail / error
- per case: id / title / status / screenshot / log path
- conclusion: PASS | FAIL | BLOCKED
```

`multica-test-orchestration` merges with API side: **one side only** verifies a given AC, missing that side → **whole ticket cannot be PASS**; errors → triage (`references/t3-failure-triage.md`).

## Why it works

UI verification bound to the actual deployed page; 1:1 with cases avoids "runs but doesn't cover"; running after G2.5 avoids a green build masking a broken environment.
