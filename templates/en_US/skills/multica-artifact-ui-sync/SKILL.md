---
name: multica-artifact-ui-sync
description: Local-first: save the UI / Interaction Design in the project repository and return only its repo-relative path; no external platform, credential, or network dependency.
metadata:
  mode: local-only
  output: artifacts/<issue-id>/ui-design.md
---

# Artifact · UI / Interaction Design Sync

## Purpose

Land the UI / Interaction Design as a stable, reviewable repository artifact. This skill is **local-only**: it does not access external platforms, read credentials, make network requests, or return URLs.

## Fixed contract

- Input: a completed Markdown artifact.
- Output: `artifacts/<issue-id>/ui-design.md`.
- Return: only that repo-relative path; absolute paths, `..`, and external links are forbidden.
- Update: overwrite the same Issue path; downstream gates become stale and must rerun after changes.

## Workflow

1. Generate Markdown containing at least: page structure, states, interactions, dimensions, and design tokens.
2. From the repository root, create `artifacts/<issue-id>/` and write `ui-design.md`.
3. Verify the file is complete and tracked by version control.
4. Return `artifacts/<issue-id>/ui-design.md` to the Leader; downstream reads that exact path.

## Common failures

- Returning a machine-local absolute path: convert it to a repo-relative path.
- Pasting only into chat: write the versioned artifact at the fixed path.
- Returning an external URL: use the fixed local path.

## Why it works

Fixed paths provide discoverability, version review, and reproducibility. With platform adapters removed, the starter remains Copy · Paste · Run without credentials or network access.
