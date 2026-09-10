---
name: multica-artifact-design-sync
description: Land technical design artifacts to the code repo or knowledge platform (default Git repo / Confluence). Used by @Architect to upload technical design for downstream implementation and test consumption. Swappable platform.
---

# Artifact · Technical Design Sync

## Purpose

Land technical design docs to the team's unified technical-doc location and let downstream retrieve them via a stable reference.

> This skill decouples "platform integration" from "role prompt": the role prompt only says "produce technical design", not which platform. Changing companies means editing only this skill, not the @Architect prompt.

## Default platform: Git repo / Confluence (choose one per team convention)

- Output: technical design (current arch, proposed change, affected components, steps, verification plan, risks).
- Upload A (Git repo): place under the repo's agreed doc dir (e.g. `docs/design/<issue-id>.md`), reviewed together with the code PR — traceable.
- Upload B (Confluence): create / update a technical design page, return the link.
- Retrieve: downstream @FrontendDev / @BackendDev / @Tester read via the **file path or page link**.

## Content spec (platform-independent part)

Per `multica-technical-design` skill: current architecture, minimal viable change, affected components, implementation steps, verification plan, risks. Keep stable headings and ids.

## Usage (role side writes only this line)

> @Architect: "Produce technical design, land it via `multica-artifact-design-sync` skill to the team's agreed location (Git / KB), and return the reference."

## Swap platform (no role-prompt change)

Replace this skill's "default platform" section with your tool (internal Wiki / Notion / Feishu), keeping the "upload + return stable reference" interface unchanged.

## Why it works

Design-doc locations vary by team (some in repo, some in Wiki). Sinking it into the skill keeps the role's "what to produce" description stable while the location swaps with the skill.
