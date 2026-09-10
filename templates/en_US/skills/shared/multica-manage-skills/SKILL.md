---
name: multica-manage-skills
description: Skill library management—batch import/export and bind SKILL.md to the Multica skill library; operates on the templates/<lang>/skills directory. The preferred mount for @Leader.
version: 1.2.0
metadata:
  operates_on: templates/<lang>/skills
  related: multica-verification
---

# Manage Skills (skill library management)

## Responsibility
Import/export the skill library as a whole and bind each `SKILL.md` to the Multica workspace skill library. This is the operational counterpart of "skill library management" used by @Leader when standing up a squad.

## Batch import/export
- Each folder under `templates/<lang>/skills` is one skill; its `SKILL.md` frontmatter `name` is the library skill name.
- Import reads every `SKILL.md`, registers it in the workspace skill library, and binds it to the agents configured in `squad-bootstrap.json`.
- Export pulls the current library back to the local tree for version control.

## Binding
- Binding follows `squad-bootstrap.json` agent→skill mapping (see `references/binding-rules.md`).
- After binding, verify each agent's required skills resolved (no missing `name`).

## Notes
- `name` in frontmatter must be unique across the library.
- This skill does not change skill content; it only manages registration/binding.
