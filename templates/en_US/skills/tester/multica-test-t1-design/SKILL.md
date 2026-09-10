---
name: multica-test-t1-design
description: T1 test design—AC↔design traceability, case templates and coverage self-check, Confluence master copy, XMind/JIRA after passphrase, Apifox scenarios and e2e planning. Integrates ac-design-trace + test-case-generator-squad.
version: 3.3.0
metadata:
  orchestrates:
    - multica-platform-jira
    - multica-platform-confluence
    - multica-platform-figma
    - multica-platform-apifox
  origin:
    - ac-design-trace-squad
    - test-case-generator-squad
---

# Test Design (T1 Test Design · Content + Landing)

## Position

**The only T1 skill**: traceability → cases → **full Confluence** → review → (after 👤 passphrase) XMind/JIRA; parallel Apifox + automation planning.  
**Not for T2/T3**—T2 see `multica-test-t2-coverage`; T3 see `-t3` + `multica-test-orchestration`.

| Layer | Skill | Responsibility |
| --- | --- | --- |
| Orchestration | `multica-test-orchestration` | Cross-phase routing; automation into repo see `references/automation-assets-lifecycle.md` |
| **T1** | **This skill** | Content + Confluence + XMind/JIRA after passphrase |
| Platform | `multica-platform-*` | Read upstream; Apifox writes scenarios |
| Review | `multica-review-test` | Review Confluence; review only, no import |

> **Three-phase delivery**: Phase A is **Confluence only** (**no XMind generated**); only Phase C after 👤 passphrase does XMind + JIRA. Details in [`references/generation-workflow.md`](references/generation-workflow.md).

## Platform Collaboration

| Platform skill | Used for |
| --- | --- |
| `multica-platform-jira` | `fetch_all` → `get_issue.py`; after passphrase `import_to_tracker.py` (team-provided, see references/import-contract.md) |
| `multica-platform-confluence` | Collect `fetch_page`; **publish** `t1-cases.md` (see § Confluence landing) |
| `multica-platform-figma` | `fetch_all` → `fetch_file.py` |
| `multica-platform-apifox` | T1 parallel write interface scenarios |
| team-knowledge-base (optional) | Step 0.5 terms/entry (binary usage; not bundled in this repo, connect per platform used) |

Credentials: `JIRA_USERNAME / JIRA_PASSWORD` preferred → see platform skill + [`data-sources.md`](references/data-sources.md).

## references/ Index

| File | Purpose |
| --- | --- |
| [`generation-workflow.md`](references/generation-workflow.md) | **Two phases, passphrase, test-management platform naming/validation, steps/priority, dedup/merge** |
| [`executability-and-permissions.md`](references/executability-and-permissions.md) | **Permission identification order, dual targets, module naming, post-generation self-check** |
| [`output-format.md`](references/output-format.md) | **JSON 1:1, generated_summary, coverage self-check table, Output Delivery** |
| [`multimodal-content.md`](references/multimodal-content.md) | HTML/image Read and fused understanding |
| [`agent-instructions.md`](references/agent-instructions.md) | Copyable Agent instructions |
| [`design-trace.md`](references/design-trace.md) | AC ↔ design traceability |
| [`test-case-template.md`](references/test-case-template.md) | Functional case fields |
| [`coverage-dimensions.md`](references/coverage-dimensions.md) | Dimension selection, scale, coverage matrix, XMind |
| [`coverage-checklist.md`](references/coverage-checklist.md) | Pre-generation self-check list |
| [`web-ui-checkpoints.md`](references/web-ui-checkpoints.md) | Figma → UI test points |
| [`api-testing-guide.md`](references/api-testing-guide.md) | Interface scenario patterns |
| [`data-sources.md`](references/data-sources.md) | Collection orchestration and credentials |

## T1 Flow

### Step 0 — Read MULTICA.md (automation path)

Issue repo matrix → each repo Read root **MULTICA.md §2** (one per split repo; one per repo must be complete). Missing → BLOCKED.

### Step 0.5 — Knowledge base (Step 0.5)

Team knowledge-base Q&A script (optional) → `--health` + Q&A. **Binary usage**: operational bucket goes into steps, rules bucket is not AC. See `generation-workflow.md`.

### Step 1 — Design traceability

[`design-trace.md`](references/design-trace.md) → write traceability table into coverage report.

### Step 2 — Collect

```bash
python scripts/fetch_all.py --jira-url "http://jira.../browse/PROJ-123" -o ./data
```

Multimodal: [`multimodal-content.md`](references/multimodal-content.md).

### Step 3–4 — Cases + self-check

By `test-case-template.md` + `generation-workflow.md` + `output-format.md` → local JSON (working file); self-check with `coverage-checklist.md`. **No XMind**.

### Step 5 — Phase A: Confluence + Apifox parallel

- Write the **full case body** to `docs/test/<ISSUE-KEY>/t1-cases.md` (template see platform-confluence `test-t1-template.md`)
- **Confluence landing** (see § below) → return link
- API contract ready → `multica-platform-apifox` supplements scenarios by contract (AI branch; write manifest planning section)
- → `multica-review-test` (review **Confluence**)
- Delivery note: `Status: pending human review (Confluence updated, not XMind / not imported to JIRA)`

### Step 6 — Phase C: XMind + JIRA (after 👤 explicit passphrase)

1. `generate_xmind.py` ← latest JSON (consistent with Confluence)
2. `import_to_tracker.py` (team-provided, interface see `references/import-contract.md`)
3. Republish Confluence status "imported to JIRA" + case-set link

## Confluence Landing (T1 · master copy)

**Parent page**: JIRA Issue Hub (PRD requirement page) **child page**.

**Local draft**: `docs/test/<ISSUE-KEY>/t1-cases.md`  
**Baseline**: `multica-platform-confluence/scripts/templates/test-t1-template.md`

Must include **each CASE step/expected body**, Apifox section, UI e2e plan (path in **MULTICA.md §2**, not hardcoded). T1/T2 **do not generate XMind**.

**Publish**:

```bash
python multica-platform-confluence/scripts/publish_design.py \
  <ISSUE-KEY> docs/test/<ISSUE-KEY>/t1-cases.md \
  --append-jira --json
```

JIRA block: `h3. T1 Test Cases (Test Cases T1)`.

## Apifox (T1 parallel)

After contract published: read API contract → `multica-platform-apifox` supplements scenarios (AI branch) → Confluence records branch/scenario → manifest path in **MULTICA.md §2**.

## Files

```text
multica-test-t1-design/
├── SKILL.md
├── config.local.env.example
├── references/
└── scripts/
```

## Why it works

T1 content and scripts are unified; **generation-workflow** + **output-format** preserve the original generator's hard rules; platform uniformly collects via REST.
