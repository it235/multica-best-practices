---
name: multica-technical-design
description: Produce the smallest viable technical plan from the PRD, acceptance criteria, and existing code, then write it to a fixed project-repository path. Use whenever architecture analysis, impact assessment, implementation steps, or a technical design document is needed; local files only, with no external platform, credential, or network dependency.
metadata:
  mode: local-only
  output: artifacts/<issue-id>/technical-design.md
---

# Technical Design

## Purpose

Produce the smallest viable technical design from the PRD (or Issue), acceptance criteria, and existing codebase, then land it as a diffable, reviewable, traceable repository file.

This skill is local-only: it does not access external platforms, read credentials, make network requests, or return external URLs.

## Inputs

- Issue identifier, such as `GOO-3`
- Repo-relative PRD / Issue path
- Code repository and baseline revision
- Applicable ACs, constraints, and explicit non-goals

If required input is missing, return BLOCKED with the missing items instead of guessing.

## Process

1. Read the PRD / Issue and acceptance criteria from the provided paths.
2. Inspect the current implementation and prefer existing patterns over broad repository scans.
3. Identify affected files, modules, services, and dependencies.
4. Select the smallest viable change and state non-goals.
5. Define executable frontend/backend steps, verification, and RISK items.
6. Write `artifacts/<issue-id>/technical-design.md`.
7. Verify the file is complete and version-controlled, then return only that repo-relative path to the Leader.

## Principles

```text
Existing patterns > new abstractions
Small changes     > big refactors
Reuse             > new dependencies
```

## Required output

| Section | Content |
| --- | --- |
| Understanding | Current behavior and requirement goal |
| Proposed change | Smallest viable plan and non-goals |
| Affected components | Files / modules / services / dependencies |
| Implementation steps | Executable steps for @FrontendDev / @BackendDev |
| Verification plan | Commands, checks, and AC mapping |
| Risks and boundaries | RISK ids, rollback points, open questions |

Fixed output:

```text
artifacts/<issue-id>/technical-design.md
```

Do not return machine-local absolute paths, paths containing `..`, or external links. Overwrite the same path for the same Issue; content changes invalidate downstream gates.

## Handoff

```text
Technical design: artifacts/<issue-id>/technical-design.md
Read this repo-relative path; revision: <commit-or-revision>.
```

If `multica-artifact-design-sync` is still mounted, it may only validate or preserve this fixed path; it must not upload the artifact or replace the path with an external reference.

## Common failures

- Drafting under `docs/design/.../design.md` before publishing creates two paths; write the fixed output directly.
- Keeping the plan only in a comment leaves no versioned artifact; write the repository file.
- Returning a platform URL or absolute path is not reproducible; return only the repo-relative path.
- Expanding scope for architectural completeness violates the smallest-change rule; return to the applicable ACs.

## Why it works

Versioning the design beside the code keeps one review chain. A fixed path lets every downstream role retrieve it without platform accounts or search while preserving smallest-change and independent-gate principles.
