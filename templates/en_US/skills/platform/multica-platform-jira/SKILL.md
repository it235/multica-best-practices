---
name: multica-platform-jira
description: Platform-layer skill (placeholder shell): read/write capability for Issue-tracking systems (JIRA-class) — Issue query, upstream-Wiki-link parsing, Story creation, transition, scheduling, description write-back, notification. Decoupled from the Wiki platform; called by artifact-orchestration skills. Concrete URLs / projects / fields live in config.yaml, never in role prompts.
metadata:
  layer: platform
  replaces: any Issue-tracking system (JIRA / ZenTao / TAPD / GitHub Issues / etc.)
---

# Platform · JIRA (placeholder shell)

> This is a **platform-layer placeholder shell**. The public multica-best-practices binds to no specific company's internal URLs or credentials.
> To onboard your own Issue system, only edit this skill's `config.yaml` and `scripts/`; all upstream roles and orchestration skills stay untouched.

## Purpose

Provide **read + write** capability for "Issue-tracking system" class platforms:

- **Read**: query Issues, parse Wiki links from descriptions, JQL / conditional search.
- **Write**: create Stories, transition states, schedule, append to description (write back Wiki links), notify.

Decoupled from `multica-platform-confluence` (Wiki); this skill only handles the Issue system, not Wiki page creation.

## Files (suggested structure)

```text
multica-platform-jira/
├── SKILL.md
├── config.yaml
├── .env.example
└── scripts/
    ├── credentials.sh
    ├── issue.sh
    └── validate.sh
```

## Read (pull Issue / locate upstream Wiki)

```bash
bash scripts/issue.sh get-issue <ISSUE-KEY>
bash scripts/issue.sh get-wiki-url <ISSUE-KEY> [text|json]
bash scripts/issue.sh search "<JQL>" [max_results]
```

**Typical chain**: `get-issue` reads acceptance criteria → `get-wiki-url` gets PRD pageId → `multica-platform-confluence` `fetch-page` pulls body.

## Write (artifact / workflow write-back)

```bash
bash scripts/issue.sh create-story --project <PREFIX> --summary "..." ...
bash scripts/issue.sh get-transitions <ISSUE-KEY>
bash scripts/issue.sh transition <ISSUE-KEY> <state_name>
bash scripts/issue.sh schedule <ISSUE-KEY> <owner> <start> <end>
bash scripts/issue.sh append-description <ISSUE-KEY> "<wiki_link_block>"
bash scripts/issue.sh notify <ISSUE-KEY> <wiki_page_id>
```

## Wiki description format

The markup syntax for the appended block depends on the target system (Jira Wiki / Markdown / plain text), implemented inside `scripts/`; characters needing escaping are handled per target-system rules.

## Workflow: Wiki-blocked degradation (PRD)

When Wiki creation fails, `multica-artifact-req-sync` may write the full PRD into the Issue description (this skill's `create-story` / `append-description`), flagged "Wiki degraded"; after recovery, create the Wiki page and update the description link.

## Relationship to artifact skills

| Orchestration skill | Calls this skill |
| --- | --- |
| `multica-artifact-req-sync` | create-story / transition / schedule / notify / get-issue |
| `multica-artifact-design-sync` | append-description (write back design Wiki link) |

## Adapting To A New Team

Edit `config.yaml`: `issue.url`, `projects.*.fields`, `field_options`, `defaults`, notification-webhook mapping.

## Why it works

Issue-system custom fields vary widely across teams; isolating them in a platform skill means Wiki / design-publish changes don't affect Issue scripts; read/write separation lets Leader / Architect reliably locate upstream Wiki artifacts from the Issue.
