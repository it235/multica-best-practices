# Skill layer architecture

> This page answers one question: **should a capability be a Skill, part of Agent Instructions, or part of the Squad?**
> And why platform URLs, credentials, and REST details **never appear in a role prompt**.

It is the full argument behind the "three-layer model" in [artifact-conventions](./artifact-conventions.md), and the design rationale for the index in `templates/en_US/skills/README.md`.

---

## 1. Why layering at all

Without layers, a Squad grows like this:

| Symptom | Consequence |
| --- | --- |
| The tracker / wiki REST scripts are copy-pasted into every role skill | Change the auth scheme and you edit the whole repo |
| Role prompts hard-code wiki space names and tracker project keys | Change team or company and the whole template set breaks |
| "What to produce" and "where to publish" live in one document | Switching platforms means re-reading everything |
| Review criteria are mixed into production criteria | Producers approve their own work and the gate is theatre |

Layering follows one principle: **things that change at different rates do not belong in the same file.**

- Content (what makes a good design) barely changes → content layer
- Platform (where to publish, how to authenticate) differs per team → platform layer
- Gluing the two together → orchestration layer

---

## 2. The four layers

```text
┌─ content ──────────────── what to write, what "good" means ────────────┐
│  multica-pm-requirement-spec / multica-technical-design                │
│  multica-backend-impl / multica-frontend-impl                           │
│  multica-test-t1-design / -t2-coverage / -t3-*                          │
└────────────────────────┬───────────────────────────────────────────────┘
                         │ called by skill name
┌─ orchestration ────────┴── land the artifact, return a stable link ────┐
│  multica-pm-artifact-publish / -design-sync / -api-sync                  │
│  multica-design-ui-impl / -frontend / -cicd-sync                     │
│  multica-test-orchestration (routing across T1/T2/T3)                  │
└────────────────────────┬───────────────────────────────────────────────┘
                         │ called by skill name
┌─ platform ─────────────┴── the only layer that touches external systems ┐
│  multica-platform-confluence / -jira / -jenkins                        │
│  multica-platform-apifox / -figma                                      │
│  URLs, credentials and REST details live here and nowhere else         │
└────────────────────────────────────────────────────────────────────────┘

┌─ review ─────────────────── executed by a non-producer ────────────────┐
│  multica-review-product / -architect / -designer                       │
│  multica-review-frontend / -backend / -test                            │
│  + multica-verification (Leader gatekeeping, independent of review)    │
└────────────────────────────────────────────────────────────────────────┘
```

**How to decide the layer**: ask "would this text be rewritten if we changed company or platform?"

- Yes → platform layer (or a config entry in the orchestration layer)
- No → content layer
- It only connects the two → orchestration layer
- It is "someone else finding faults" → review layer

---

## 3. Skill inventory (29)

### Content

| Skill | Mounted by | Responsibility |
| --- | --- | --- |
| `multica-pm-requirement-spec` | ProductManager | Structure a request into a numbered PRD |
| `multica-technical-design` | Architect | Technical design draft (with metadata and revision log) |
| `multica-backend-impl` | BackendDev | Contract-first, TDD backend implementation |
| `multica-frontend-impl` | FrontendDev | Frontend implementation with complete UX states |
| `multica-test-t1-design` | Tester | T1 cases: traceability matrix + coverage dimensions |
| `multica-test-t2-coverage` | Tester | T2 coverage assessment (against T1 and the implementation diff) |
| `multica-test-t3-ui-automation` | Tester | T3 UI automation (1 CASE = 1 test) |
| `multica-test-t3-api-automation` | Tester | T3 API automation batch run |
| `multica-verification` | Leader | Gatekeeping: is the evidence complete, do the ACs line up |


### Orchestration

| Skill | Mounted by | Landing target (swappable) |
| --- | --- | --- |
| `multica-pm-artifact-publish` | ProductManager | requirements platform (default wiki + tracker) |
| `multica-artifact-architect` | Architect | docs platform / Git |
| `multica-artifact-backend` | BackendDev | API platform (default Apifox) |
| `multica-design-ui-impl` | Designer | design platform (default Figma) |
| `multica-artifact-frontend` | FrontendDev | docs platform |
| `multica-artifact-cicd-sync` | DevOps | CI (default Jenkins) → returns the deploy URL |
| `multica-test-orchestration` | Tester | Routing and adjudication across T1/T2/T3 |

### Platform

| Skill | Read | Write |
| --- | --- | --- |
| `multica-platform-jira` | issues, linked issues, wiki links | create story, transition, append description / link |
| `multica-platform-confluence` | pages (URL / pageId → Markdown + images) | create / update pages (Markdown / HTML) |
| `multica-platform-figma` | file metadata, design summary | — |
| `multica-platform-apifox` | scenarios / contract | OpenAPI sync, scenario supplement, batch run |
| `multica-platform-jenkins` | build status, logs | trigger build / release / promote |
| `multica-platform-knowledge-base` | knowledge-base Q&A | — |

> Platform skills are **placeholder shells only**: `config.yaml` and `.env.example` contain nothing but `<JIRA_URL>`, `<JENKINS_URL>` and friends. Teams fill in their own values. See [platform-collaboration](./platform-collaboration.md).

### Review

| Skill | Reviewer | What it reviews |
| --- | --- | --- |
| `multica-review-product` | ProductReviewer | value / logic / clarity |
| `multica-review-architect` | ArchReviewer | design dimension coverage and blockers |
| `multica-review-designer` | DesignReviewer | UI alignment with the requirement |
| `multica-review-frontend` | FrontendReviewer | edge states, blast radius, 8 dimensions |
| `multica-review-backend` | BackendReviewer | contract, error handling, compatibility |
| `multica-review-test` | TestReviewer | case executability and coverage honesty |

### Tooling

| Skill | Purpose |
| --- | --- |
| `multica-manage-skills` | Operational statistics through the Multica API |

---

## 4. Role → skill mounting matrix

| Role | Content | Orchestration | Platform (only the orchestration layer calls it) |
| --- | --- | --- | --- |
| ProductManager | `multica-pm-requirement-spec` | `multica-pm-artifact-publish` | via orchestration |
| Architect | `multica-technical-design` | `multica-artifact-architect` | via orchestration |
| Designer | — | `multica-design-ui-impl` | via orchestration |
| BackendDev | `multica-backend-impl` | `multica-artifact-backend` | via orchestration |
| FrontendDev | `multica-frontend-impl` | `multica-artifact-frontend` | via orchestration |
| Tester | `multica-test-orchestration` → T1/T2/T3 | case prose published by T1/T2 itself | via orchestration |
| DevOps | — | `multica-artifact-cicd-sync` | `multica-platform-jenkins` |
| Leader | `multica-verification` | — | — |
| Reviewer | `multica-review-*` | — | — |

**Read the last two columns carefully**: only DevOps mounts a platform skill directly (operating CI *is* its job). Every other role mounts **content / orchestration skills only**; the platform is called by name from the orchestration layer.

---

## 5. Mounting conventions

1. **Mount by name, never by path**: Agent Instructions write `` `multica-xxx` ``, never `templates/...`.
2. **No platform names in role prompts**: write "land it with `multica-artifact-backend` and return a stable link", not "publish to Apifox".
3. **No credentials in any prompt**: environment variables or the platform skill's `.env` only — see [SECURITY](../../SECURITY.md).
4. **The orchestration layer does not re-implement the platform**: if the platform already has a REST script, call it; do not copy it.

---

## 6. Common mistakes

| Bad | Better |
| --- | --- |
| "Publish the design doc under page X of space Y" in Agent Instructions | "Land it with `multica-artifact-architect` and return the link" — parent-page config stays in the platform skill |
| A role skill carrying its own tracker Basic-auth code | Delete it; declare `metadata.orchestrates: multica-platform-jira` instead |
| Letting the producer review its own output | Review runs through `multica-review-*` + a non-producer — see [gates-and-evidence](./gates-and-evidence.md) |
| One skill that both defines "how to write a case" and "how to connect to the tracker and import" | Split it: content stays in T1, connection stays in the platform; tool-specific import scripts live in your own T1 |

---

## 7. Further reading

| Document | Content |
| --- | --- |
| [artifact-conventions](./artifact-conventions.md) | Artifact content spec + orchestration skill usage |
| [platform-collaboration](./platform-collaboration.md) | The "platform capability written once" convention in detail |
| [FLOW](./FLOW.md) | Deliverable-driven end-to-end flow and gates |
| [where-to-put-things](./where-to-put-things.md) | Cheat sheet: where does an instruction go |
