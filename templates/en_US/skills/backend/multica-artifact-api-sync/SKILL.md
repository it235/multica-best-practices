---
name: multica-artifact-api-sync
description: Land API contract artifacts to the API collaboration platform (default Apifox). Used by @BackendDev to upload API contract for downstream frontend / test consumption. Swappable platform.
---

# Artifact · API Contract Sync

## Purpose

Land API contract artifacts to the team's unified API platform and let downstream (frontend / test) retrieve them via a stable reference.

> This skill decouples "platform integration" from "role prompt": the role prompt only says "produce API contract", not which platform. Changing companies (Swagger / Postman / YApi / internal gateway) means editing only this skill, not the @BackendDev prompt.

## Default platform: Apifox

- Output: API contract (endpoints, in/out params, error codes, auth, state-machine boundaries).
- Upload: maintain interface definitions in Apifox, export / sync, then use the **project / interface-group link** as the artifact reference.
- Retrieve: downstream @FrontendDev / @Tester read via the link — the link is the stable reference.

## Content spec (platform-independent part)

Per the stage convention, the API contract at least contains: endpoint list, request/response schema, error-code table, auth method, mapping to BR- business rules.

## Usage (role side writes only this line)

> @BackendDev: "Produce API contract, land it via `multica-artifact-api-sync` skill to the team API platform, and return the link."

## Swap platform (no role-prompt change)

Replace this skill's "default platform" section with your tool (Swagger / YApi / Postman / internal gateway), keeping the "upload + return stable link" interface unchanged.

## Why it works

API platforms differ by team; hard-coding the platform name into the role prompt freezes it. Sinking it into the skill keeps the role's "what to produce" description stable while the platform swaps with the skill.
