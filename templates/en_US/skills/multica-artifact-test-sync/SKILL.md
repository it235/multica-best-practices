---
name: multica-artifact-test-sync
description: Local-first: save the Test Cases / Report in the project repository and return only its repo-relative path; no external platform, credential, or network dependency.
metadata:
  mode: local-only
  output: artifacts/<issue-id>/test-cases.md
---

# Artifact · Test Cases / Report Sync

## Purpose

Land the Test Cases / Report as a stable, reviewable repository artifact. This skill is **local-only**: it does not access external platforms, read credentials, make network requests, or return URLs.

## Fixed contract

- Input: a completed Markdown artifact.
- Output: `artifacts/<issue-id>/test-cases.md`.
- Return: only that repo-relative path; absolute paths, `..`, and external links are forbidden.
- Update: overwrite the same Issue path; downstream gates become stale and must rerun after changes.

## Workflow

1. Generate Markdown containing at least: happy paths, boundaries, failures, empty/no-permission states, and AC mappings.
2. From the repository root, create `artifacts/<issue-id>/` and write `test-cases.md`.
3. Verify the file is complete and tracked by version control.
4. Return `artifacts/<issue-id>/test-cases.md` to the Leader; downstream reads that exact path.

## Common failures

- Returning a machine-local absolute path: convert it to a repo-relative path.
- Pasting only into chat: write the versioned artifact at the fixed path.
- Returning an external URL: use the fixed local path.

## Why it works

Fixed paths provide discoverability, version review, and reproducibility. With platform adapters removed, the starter remains Copy · Paste · Run without credentials or network access.
