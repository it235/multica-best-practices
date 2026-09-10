# Not sure where an instruction goes?

> This is the most valuable page in this repo. Remember it — worth more than reading 100 prompts.

## Cheat sheet

| I want to tell the agent… | Put it in |
| --- | --- |
| "What we're doing this time" | Issue |
| "What background does this project have" | Project Instructions |
| "What role are you" | Agent Instructions |
| "Who is responsible for what" | Squad Instructions |
| "Where do stage artifacts go / how does downstream read" | landed by the `multica-artifact-*` skill to the team platform, returning a stable link (see [artifact-conventions](./artifact-conventions.md)) |
| "Should this capability be a Skill, a role prompt, or a platform script" | [role-skills-architecture](./role-skills-architecture.md) (four layers) |
| "Where do platform URLs / credentials / REST details go" | only in the `multica-platform-*` layer (see [platform-collaboration](./platform-collaboration.md)) |
| "How do I trim the full flow, what runs first" | [FLOW](./FLOW.md) (deliverable-driven, not a role assembly line) |
| "How do split / multiple repos get routed" | [multi-repo-and-issue-links](./multi-repo-and-issue-links.md) |
| "Which directory do automation scripts go in inside the product repo" | `MULTICA.md` at the target repo root (see [test-automation-in-repo](./test-automation-in-repo.md)) |
| "How to do a certain kind of check" | Skill |
| "Tests must pass" | CI (engineering system) |
| "Who decides what ships" | Human |

## Mental model

```text
Issue    ↓ What are we doing?
Project  ↓ What should we know?
Agent    ↓ What is my job?
Squad    ↓ Who does what?
Skill    ↓ How do I do it?
CI / PR  ↓ What must actually pass?
```

## One-liner version

```text
Agent  = Role
Skill  = Method
Squad  = Coordination
Issue  = Task
CI     = Enforcement
```

## The most common mistake

Stuffing everything into one "omniscient" Agent prompt:

```text
You are an all-round software development expert. You need to analyze requirements,
design the architecture, write code, test, review, and make sure the final task is done.
```

❌ It occupies Agent, Squad, Skill, and Issue at the same time. Change the task, the team, or the process and all of it breaks.

✅ The correct split:

- Agent Instructions: **who I am** (implement the confirmed design)
- Squad Instructions: **who does what** (frontend implementation → FrontendDev / backend implementation + API contract → BackendDev (per the Issue scope, skipped if missing); gatekeeping → Leader with the multica-verification skill; business review → Reviewer)
- Skill: **how** (the rules for doing the work)
- Issue: **what** (this task's goal and acceptance criteria)

## Related

- Concrete bad examples: [`common-mistakes.md`](./common-mistakes.md)
- How to cut down and extend: [`adapt-and-scale.md`](./adapt-and-scale.md)
