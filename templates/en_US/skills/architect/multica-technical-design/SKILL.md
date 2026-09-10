---
name: multica-technical-design
description: Produce a minimal technical plan based on the existing code. Used for architecture analysis, impact assessment, and implementation-plan design.
---

# Technical Design

## Purpose

Produce the smallest viable technical plan based on the existing codebase.

## Process

1. Inspect the current implementation.
2. Identify the relevant modules.
3. Identify the existing patterns.
4. Determine the smallest viable change.
5. Identify dependencies.
6. Identify risks.
7. Define the verification method.

## Principles

```text
Existing patterns > new abstractions
Small changes     > big refactors
Reuse            > new dependencies
```

## Output

- Current architecture
- Proposed changes
- Affected components
- Implementation steps
- Verification plan
- Risks

## Why this works

"The smallest viable change" is a verifiable principle: the smaller the change, the easier it is to verify (Leader rerun / Tester regression), and the lower the regression risk.
