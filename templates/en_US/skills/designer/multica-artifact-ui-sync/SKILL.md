---
name: multica-artifact-ui-sync
description: Land UI / interaction design artifacts to the design collaboration platform (default Figma). Used by @Designer to upload visuals and return a stable link for downstream frontend consumption. Swappable platform.
---

# Artifact · UI Design Sync

## Purpose

Land UI design artifacts to the team's unified design platform and let downstream (frontend) retrieve them via a stable reference.

> This skill decouples "platform integration" from "role prompt": the role prompt only says "produce UI design", not which platform. Changing companies (Zeplin / 蓝湖 / MasterGo) means editing only this skill, not the @Designer prompt.

## Default platform: Figma

- Output: Figma file link + annotations (color / spacing / font / components) + exports.
- Upload: complete the design in Figma, then use the **file link** and **key Frame links** as the artifact reference.
- Retrieve: downstream @FrontendDev reads via the link — the link is the stable reference, no local file dependency.

## Content spec (platform-independent part)

Regardless of platform, the UI artifact at least contains:
- Page / module structure (aligned to PRD information architecture)
- States: empty, loading, error, no-permission
- Interaction: entry, navigation, validation feedback
- Annotations: size, spacing, color values, font, component boundaries

## Usage (role side writes only this line)

> @Designer: "Produce UI design, land it via `multica-artifact-ui-sync` skill to the team design platform, and return the link to the Leader."

## Swap platform (no role-prompt change)

Replace this skill's "default platform" section with your tool (蓝湖 / Zeplin / MasterGo / internal design library), keeping the "upload + return stable link" interface unchanged.

## Why it works

Platforms differ greatly across teams; hard-coding the platform name into the role prompt freezes it. Sinking it into the skill keeps the role's "what to produce" description stable while the platform swaps with the skill.
