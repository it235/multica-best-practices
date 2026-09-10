# Naming Convention: Role + Project + Member ID

> Purpose: one role definition can be instantiated as multiple Agents, distinguished by name instead of edited instructions — so the flow stays reusable. When a project has several members of the same role (e.g. multiple front-end devs), "role + project" alone still collides, so a third member-id segment is needed.

## Rules

1. Agent name = `<role>-<project>-<member-id>`, where the role comes from a fixed vocabulary.
2. Role vocabulary: `Leader / ProductManager / Architect / Designer / FrontendDev / BackendDev / Tester / Reviewer`
3. `<project>` = service / domain / project name (lowercase hyphenated), e.g. `user-service`, `web`, `order`.
4. `<member-id>` = the member's unique ID within "this project + this role", using an **employee number or nickname** (e.g. `u1024`, `ajie`). Do NOT use a full real name (avoids PII and cross-project ambiguity for the same person).
5. The name only distinguishes instances; it carries no responsibility. Responsibilities always come from Agent Instructions / Squad Instructions.
6. `Architect` is technical architecture design (change plan / files / verification); `Designer` is UI / interaction design (design platform decided by the `multica-design-ui-impl` skill). Different expertise and artifacts — don't merge them.

## Examples

| Role | Example name | Meaning |
| --- | --- | --- |
| BackendDev | `BackendDev-user-service-u1024` | User-service backend (member u1024) |
| FrontendDev | `FrontendDev-web-ajie` | Web frontend (member nickname ajie) |
| Tester | `Tester-order-lina` | Order-domain testing (member nickname lina) |
| Architect | `Architect-core-u2031` | Core architecture design (member u2031) |
| Designer | `Designer-web-mei` | Web UI / interaction design (platform decided by skill, nickname mei) |
| Leader | `Leader-core-u0001` | Core squad Leader (member u0001) |

> The three-segment form resolves the "real name vs role name" collision: the role keeps the name readable and routable; the project segment isolates services; the member-id (employee number / nickname) uniquely distinguishes "same project, same role, multiple people". Templates use the placeholder `<member>` instead of a real name, preserving Copy-Paste-Run.

## Squad instance suffix & prefix wildcard

Squad Instructions refer to members by the **role prefix** (`@Architect` / `@FrontendDev` / …), not a hardcoded full Agent name — that's what keeps `squad.md` copy-paste-ready. But a workspace routinely hosts multiple instances of the same role (e.g. `FrontendDev-web-ajie`, `FrontendDev-web-lina`); the orchestrator must be able to pin the one that belongs to *this* squad. Rules:

1. Each squad declares its **instance suffix** `suffix` (e.g. `payment`, `order`) at startup, bound to all its roles; it maps to the `<project>` segment above.
2. Wherever the Squad Instructions write `@role`, the orchestrator resolves it to `@role-<squad suffix>-<squad member>` before dispatching the precise @mention.
   - Example: with `suffix = payment` and `member = u1024`, `@FrontendDev` → actually dispatched to `FrontendDev-payment-u1024`, `@Architect` → `Architect-payment-u1024`.
3. If a role is out of the squad's scope (the Issue 【Scope】 doesn't include that layer), skip its artifact per the existing rule — don't resolve, don't dispatch.
4. `suffix` and `member` are set once in the squad configuration, never written into `squad.md`; `squad.md` always shows only the role prefix, staying copy-paste-ready.

> Thus the "role prefix" is the logical name inside the Squad, and `@role-project-member-id` is the physical name inside the workspace; the two are bridged by the squad configuration.

## Why

- In Multica, Agent names must be unique; multiple instances of the same role are the norm (multi-service / multi-domain), so names must be distinguishable.
- The role is in the name, so `@mention` routing is readable and unambiguous — `@BackendDev-user-service` tells you who it is at a glance.
- **Changing the name doesn't change behavior; changing behavior means editing Instructions, not the name**: switching instances only changes `<instance>`, and the template is reused as-is.
- Naming is the last piece that makes "reusable flows" work: the same `squad.md`, with a different set of instance names, is a brand-new squad.
- **The prefix wildcard solves "coexisting instances"**: Squad instructions only write the role prefix (reusable); the squad configuration supplies the suffix (locatable). Separating the two keeps reuse intact while still letting the orchestrator dispatch precisely to this squad's members in a crowded workspace.
