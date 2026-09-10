---
name: multica-artifact-req-sync
description: Land product requirement / PRD artifacts to the requirement knowledge platform (default Confluence). Used by @ProductManager to upload PRD and return a link for downstream design / dev / test consumption. Swappable platform.
---

# Artifact · Requirement Sync

## Purpose

Land product requirement artifacts to the team's unified requirement platform and let downstream retrieve them via a stable reference.

> This skill decouples "platform integration" from "role prompt": the role prompt only says "produce PRD", not which platform. Changing companies (Wiki / Yuque / Feishu / internal KB) means editing only this skill, not the @ProductManager prompt.

## Default platform: Confluence

- Output: PRD (or MRD / dashboard spec / cross-system spec / acceptance checklist, by type).
- Upload: create / update a page in Confluence, keeping G-/FR-/BR-/AC-/KPI-/OP-/RISK- ids and stable headings (see `docs/en_US/gates-and-evidence.md` AI-readable discipline).
- Retrieve: downstream @Architect / @Designer / @FrontendDev / @BackendDev / @Tester read via the **page link** — the link is the stable reference.

## Content spec (platform-independent part)

PRD at least contains (see @ProductManager role instruction): one-line definition, background, goals G- + KPI-, users & permissions, scope, FR-/BR-/AC-, field definitions, empty/error/no-permission states, RISK-/OP-, revision log.

## Usage (role side writes only this line)

> @ProductManager: "Produce PRD, land it via `multica-artifact-req-sync` skill to the team requirement platform, and return the page link."

## Swap platform (no role-prompt change)

Replace this skill's "default platform" section with your tool (Yuque / Feishu / Notion / internal Wiki), keeping the "upload + return stable link" interface unchanged.

## Why it works

Platforms differ greatly across teams; hard-coding the platform name into the role prompt freezes it. Sinking it into the skill keeps the role's "what to produce" description stable while the platform swaps with the skill.
