---
name: multica-artifact-req-sync
description: Land PRD artifacts as repository-local Markdown by default and return a stable reference; opt into an external platform adapter only when the team explicitly needs one.
---

# Artifact · Requirement Sync

## Purpose

Turn a PRD into a stable reference that downstream can retrieve. This skill does not generate PRD content. Its zero-dependency default is repository-local Markdown; platform skills are optional adapters.

> This skill decouples "platform integration" from "role prompt": the role prompt only says "produce PRD", not which platform. Changing companies (Wiki / Yuque / Feishu / internal KB) means editing only this skill, not the @ProductManager prompt.

## Modes

| Mode | Use when | Stable reference |
| --- | --- | --- |
| `local` (default) | No external requirement/task platform is needed | Repo-relative `artifacts/<issue-id>/prd.md` |
| `external` (explicit opt-in) | The team intentionally synchronizes to a requirement/task platform | Platform page or task URL |

## Local workflow (default)

```bash
bash scripts/publish-local.sh \
  --issue-id <ISSUE-ID> \
  --input <PRD.md> \
  --root artifacts
```

Return the printed repo-relative path, such as `artifacts/GOO-3/prd.md`. This mode reads no credentials, makes no network request, and creates no external task. Updating a requirement keeps the same path and updates the PRD revision log; downstream gates become stale according to the Squad rules.

## External workflow (optional)

Only when the Issue or team configuration explicitly requires it, call the relevant `multica-platform-*` adapter and return its URL. If external publishing fails, never claim success: fall back to `local` only when external landing was optional and state the reason; otherwise report BLOCKED.

## Content spec (platform-independent part)

PRD at least contains (see @ProductManager role instruction): one-line definition, background, goals G- + KPI-, users & permissions, scope, FR-/BR-/AC-, field definitions, empty/error/no-permission states, RISK-/OP-, revision log.

## Usage (role side writes only this line)

> @ProductManager: "Produce PRD, land it via `multica-artifact-req-sync`, and return the stable reference. Use local mode unless the Issue explicitly requires an external platform."

## Configuration

- Local mode needs no configuration. `--root` defaults to `artifacts`; use a repository-relative path only, never an absolute path or `..`.
- External mode keeps configuration and credentials inside its `multica-platform-*` skill.

## Why it works

A stable reference does not have to be an external URL. The repository path keeps the starter copy-paste-ready without credentials, while optional adapters preserve platform integration without changing the role prompt or PRD schema.
