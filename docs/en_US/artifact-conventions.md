# Artifact Conventions

> Purpose: in multi-agent collaboration, downstream agents must be able to **find upstream artifacts via a stable reference**. This doc defines the "content spec" and the "sync skill" for each artifact — **where the artifact lands and how it is uploaded/retrieved is the skill's job, never written into the agent prompt**. So when a company changes platforms, only the skill changes; no agent is touched.

## 1. Core principle: content belongs to the role, landing method belongs to the skill

- **Agent prompts only describe "what content to produce"** (e.g. which sections a PRD has, which fields an API contract has). **No specific platform name appears** (Figma / Confluence / Apifox / Jira, etc.).
- **Landing / upload / retrieval is handled by the `multica-artifact-*-sync` skill family.** Each role writes only one line in its prompt: "use `multica-artifact-xxx-sync` to land it". The skill may write directly to the repository or call a swappable platform adapter.
- **Stable reference = link or path**: downstream locates upstream artifacts via the link/path returned by the skill, not via "you should know what upstream produced".

## 1.1 Three-layer architecture: content / orchestration / platform

To make "switch company, switch only the skill" actually hold, artifact landing splits into three layers — the deeper, the more internal; the higher, the more reusable:

| Layer | Who | What it writes | Contains internal details? |
| --- | --- | --- | --- |
| **Content** | Role prompts (agents/*.md) | What content to produce (sections, fields, numbering) | No — never a platform name |
| **Orchestration** | `multica-artifact-*-sync` skills | Land content as an artifact class (PRD / design / API / cases), return stable reference | No — selects a repo path or platform skill, no URL |
| **Platform** | `multica-platform-*` skills | Actually connect the system: Wiki / Issue / CI / test tool read/write | **Yes — URLs, spaces, Job names, credentials live here** |

**Key constraints**:

1. The content layer (roles) never names a platform; it only says "use `multica-artifact-xxx-sync` to land it".
2. The orchestration layer (`multica-artifact-*-sync`) may write to a safe repo-relative path or call a platform-layer skill; it never hardcodes a URL / pageId / Job name.
3. The platform layer (`multica-platform-*`) is the **only** place allowed to hold internal URLs, space IDs, and credential variables; and credentials only go through runtime env, never into any prompt.

So: the public repo ships only content + orchestration + **platform-layer placeholder shells**; a team onboarding its own internal network only fills the shell's `config.yaml` and `scripts/`, with zero changes upstream.

### Standard usage (PM / Architect dual-skill phrasing)

- **@ProductManager**: first structure the Issue into a numbered PRD with `multica-requirement-analysis`, then land it via `multica-artifact-req-sync` (repository-local Markdown by default; call the platform layer only when explicitly enabled).
- **@Architect**: first write the local design doc with `multica-technical-design`, then publish via `multica-artifact-design-sync`.
- **@Tester**: first produce cases with `multica-test-design`, then land via `multica-artifact-test-sync`; T3 automation uses `multica-test-automation`.

The "analysis / design" skills own **content**; the "artifact-sync" skills own **landing & reference return** — separation makes content reusable and platform swappable.

## 2. Artifact → content spec → sync skill (one-to-one)

| Artifact | Owner | Content spec (role side) | Sync skill (platform side, swappable) |
| --- | --- | --- | --- |
| UI design | @Designer | page structure, states, interaction, annotations (aligned to PRD IA) | `multica-artifact-ui-sync` (default Figma) |
| Product requirement PRD | @ProductManager | G-/FR-/BR-/AC-/KPI-/RISK-/OP- numbered requirements | `multica-artifact-req-sync` (default `artifacts/<issue-id>/prd.md`; external platform optional) |
| Technical design doc | @Architect | current arch, minimal change, affected components, steps, risks | `multica-artifact-design-sync` (default Git repo / Wiki platform) |
| API contract | @BackendDev | endpoints, in/out params, error codes, auth, BR- mapping | `multica-artifact-api-sync` (default API tool) |
| Test cases / report | @Tester | feature/api cases, AC- coverage, test report | `multica-artifact-test-sync` (default case platform) |
| CI/CD deployment | @DevOps | build/deploy records, env URL, log summary | `multica-artifact-cicd-sync` (default CI system) |

> Code artifacts live in the real code repo; the changed-file list is written into the corresponding stage artifact file for downstream/gate review.

## 3. Role-side template (uniform)

Each role's "WHAT I PRODUCE" section writes only:

```text
Produce <artifact>, land it via `multica-artifact-<xxx>-sync` skill to the team's agreed platform, and return a stable link to the Leader.
Content spec: see section 2 / the role instruction.
```

No platform name, no local path, no "upload to XXX".

## 4. Hard rules for downstream references

1. After upstream finishes, the skill returns a **stable link/path**; the Leader includes that reference explicitly when dispatching (e.g. "read `<PRD link>` then do X"), never by word of mouth.
2. Gate verdicts reference artifacts by "link + id" (e.g. "`<API contract link>` BR-3 missing error code"), not "that doc earlier".
3. The same artifact type always lands via the same skill — downstream locates by skill name + issue id, not by search.
4. When an artifact is modified, the reference stays, content updates; downstream gates must re-judge (see gates' "artifact change invalidates gate").

## 5. Relation to the numbering spec

- Artifact **content** uses `gates-and-evidence.md`'s "AI-readable discipline" (stable headings, stable table fields, G-/FR-/BR-/AC- ids).
- Artifact **location** is decided by the skill (link or path); both location and content must be stable for machine-localizable downstream consumption.

## 6. Platform swap (no agent change)

A stable reference may be a repo-relative path or an external URL. Requirement artifacts default to `artifacts/<issue-id>/prd.md`, requiring no credentials or external system; enable a `multica-platform-*` adapter only when the team explicitly needs synchronization. For other artifacts, swap the adapter inside the corresponding `multica-artifact-*-sync` skill while preserving the “land + return stable reference” interface. Role prompts and squad instructions **need no change**.

## 7. Common mistakes

Bad: "@Designer upload the design to Figma and send me the link." (platform name hard-coded into the prompt; breaks on platform change)

Better: "@Designer produce UI design, land it via `multica-artifact-ui-sync` skill and return the link." (platform lives in the skill; prompt stays copy-pasteable)
