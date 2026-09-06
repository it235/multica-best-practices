# Platform skill collaboration conventions

> Goal: **platform capability is written exactly once** (`multica-platform-*`). Role / phase skills only declare *what they read, what they write, and who they call* — they never repeat REST details or credential instructions.

## 1. Three layers (consistent with `artifact-conventions`)

```text
content / phase skill     what to write, when (multica-test-t1-design, multica-technical-design …)
        ↓ calls by name
platform skill            how to read / write the tracker, wiki, API platform, design tool …
        ↓
team platform API         tracker / wiki / API platform / design tool / CI …
```

- **Agent Instructions never contain platform URLs or REST details** — only skill names.
- **One credential priority everywhere**: environment variables (`ATLASSIAN_USER` / `ATLASSIAN_PASS`, …) → the role skill's `.env` → the platform skill's `config.yaml` (see `SECURITY.md`). Platform skills ship **placeholders only**; teams fill in their own values.
- Every skill that touches a platform declares `metadata.orchestrates` (or `metadata.uses_platform`) in its frontmatter and carries a **"Platform collaboration"** section in the body.

## 2. Platform skill overview

| Platform skill | Read | Write |
| --- | --- | --- |
| `multica-platform-jira` | get-issue, get-wiki-url, resolve-parent-page-id | create-story, transition, append-description, append-artifact-link |
| `multica-platform-confluence` | `fetch_page.py`, `fetch_page_by_url.py` | `publish_design.py`, PRD HTML |
| `multica-platform-figma` | `fetch_file.py` | — |
| `multica-platform-apifox` | scenarios / contract queries | `sync_openapi.js`, scenario supplement, `run_apifox.py` |
| `multica-platform-jenkins` | status / logs | `trigger_env.py` |

## 3. Role / phase skill → platform (standard matrix)

| Skill | Tracker | Wiki | Design | API platform | CI |
| --- | --- | --- | --- | --- | --- |
| `multica-artifact-req-sync` | read+write | read+write | — | — | — |
| `multica-artifact-design-sync` | read + write back link | read+write | — | — | — |
| `multica-artifact-api-sync` | read + write back | read+write | — | write (OpenAPI) | — |
| `multica-artifact-frontend` | read + write back | read+write | read (link) | — | — |
| `multica-artifact-ui-sync` | — | optional read | read + link | — | — |
| `multica-test-t1-design` | read | read + write case prose | read | write (scenarios) | — |
| `multica-test-t2-coverage` | — (material comes from the Issue comment) | read+write increment | — | optional scenario top-up | — |
| `multica-test-t3-*` | — | report into the comment | — | run batch | — |
| `multica-artifact-cicd-sync` | optional Issue read | — | — | — | read+write |

## 4. T1 fetch consolidation (done)

| Capability | Implementation |
| --- | --- |
| Read an Issue, parse wiki / design links | `multica-platform-jira` → `get_issue.py` / `jira_cli.py get-issue` |
| Read wiki prose (URL, images, child pages) | `multica-platform-confluence` → `fetch_page_by_url.py` |
| Read design files | `multica-platform-figma` → `fetch_file.py` |
| Orchestration entry point | `multica-test-t1-design` → `fetch_all.py` (locates the platform scripts by skill name) |

**Do not** merge case JSON templates and coverage checklists into the platform layer — those stay in `multica-test-t1-design/references/`.

**Do not** put "bulk-import cases into the test management tool" into the platform layer either — it binds to a specific tool. Keep it in your team's own T1 skill, and only run it after a human go-ahead.

## 5. Standard `SKILL.md` block (copy this)

Any skill with a non-empty `metadata.orchestrates` adds:

```markdown
## Platform collaboration

| Platform skill | How this skill uses it |
| --- | --- |
| `multica-platform-jira` | … |
| `multica-platform-confluence` | … |

Credentials and CLI details live **only in the platform skill** — this skill does not duplicate them.
```

A content skill (e.g. `multica-backend-impl`) that only reads upstream **indirectly** may write `uses_platform: via artifact-* / Issue hub` or a short Platform collaboration table instead.

## 6. Common mistakes

Bad: "Write the tracker Basic-auth steps again inside `multica-test-t1-design`."

Better: "Read `multica-platform-jira/SKILL.md`; T1 only describes the `fetch_all` order."

Bad: "Architect and Tester each maintain their own wiki fetch."

Better: "Use `fetch_page_by_url.py` in both; Tester's `fetch_all` calls the platform CLI by skill name."
