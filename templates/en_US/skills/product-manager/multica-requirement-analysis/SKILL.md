---
name: multica-requirement-analysis
description: Turn an Issue into a clear, actionable engineering task. Used for requirement clarification, scope confirmation, and acceptance-criteria definition.
---

# Requirement Analysis

## Purpose

Turn an Issue into a clear, actionable engineering task.

## Process

1. Identify the business goal.
2. Identify the expected behavior.
3. Identify the explicit scope.
4. Identify the non-goals.
5. Identify the constraints.
6. Identify the acceptance criteria.
7. Identify ambiguities.
8. Identify dependencies.

## Output

- **Goal**: what problem to solve
- **Scope**: what will change
- **Non-goals**: what explicitly won't change
- **Acceptance criteria**: testable check items
- **Constraints**: compatibility / performance / security / time
- **Dependencies**: prerequisites
- **Open questions**: items needing clarification

## Rule

Don't silently digest ambiguous requirements.

If an ambiguity would materially affect the implementation:

→ BLOCKED
→ Ask for clarification.

## Why this works

Ambiguity at the requirement stage gets amplified at every later stage. Blocking ambiguity with BLOCKED is far cheaper than letting 5 Agents each guess differently.
