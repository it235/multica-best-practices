# Multi-repo and linked requirements

This page covers two things: how **multi-repo requirements** are identified and routed in a Squad, and whether (and how) each role must read **linked Issues** upstream.

---

## 1. Multi-repo requirements

### 1.1 Can Multica / the Squad detect this automatically?

**No.** Multica does not scan your Git organisation or your tracker fields to infer which repos are involved.

**Single source of truth**: the **repo matrix** in the Issue template (see `templates/en_US/squad/*/issue.md`). The Leader dispatches work from it at G0; DevOps triggers CI per repo from it.

### 1.2 What the Issue must state

| Field | Meaning |
| --- | --- |
| **Repo layout** | single repo / split repos / **multi-repo (≥2 independent repos)** |
| **Repo matrix** | one row per repo: repo name, CI service id, **`MULTICA.md`** (required at the root), deploy / feature branch |
| **Deploy branch** | **same name in every repo** (default `release/<ISSUE-KEY>-<slug>`); CI only builds the deploy branch |
| **Scope checkboxes** | a side that is not checked gets no role dispatched; a repo with no change is marked **N/A** in its row |

Example:

```markdown
| Repo | Service (CI) | Deploy branch | Feature branch |
| --- | --- | --- | --- |
| acme-frontend | acme-web | release/PROJ-123-foo | feature/PROJ-123-frontend-foo |
| acme-api | acme-api | release/PROJ-123-foo | feature/PROJ-123-backend-foo |
| shared-lib | — | N/A (no change in this requirement) | — |
```

### 1.3 Leader / DevOps / implementer split

| Role | Multi-repo behaviour |
| --- | --- |
| **Leader** | verify the matrix is complete at G0; at G2 require that **every repo**'s change is merged to its own deploy branch; paste each repo's SHA/MR into the comment |
| **FrontendDev / BackendDev** | work only in the repo that is theirs in the matrix; never guess another repo's branch name |
| **DevOps** | call `multica-artifact-cicd-sync` / CI for every row that needs deploying; return **each environment's URL** |
| **Tester T2/T3** | assemble the SHA/MR of **all** repos from the comments; abort if any is missing |

### 1.4 Common failures

- The Issue says "frontend and backend are split" but names no repo → DevOps has no service id to trigger
- One repo merged to the deploy branch while another is still on a feature branch → G2 must not PASS
- Assuming a Multica workspace bound to multiple repos routes automatically → **wrong**; a human must fill in the Issue matrix

---

## 2. Linked Issues upstream

### 2.1 Can the platform read them?

`multica-platform-jira` (`get_issue.py` / `jira_cli.py get-issue`) returns a **`linked_issues`** array (link type, direction, key, summary, status).

Optional **`--with-linked`**: pull one more level — the description and tracker/design links of each linked Issue (useful when this requirement iterates on a previous one).

### 2.2 Must each role read them?

**Yes.** **Reading upstream** before starting must include:

1. The **current Issue**: description + comments + attachments
2. **`linked_issues`** whose type is Relates / Blocks / "is blocked by" / "cloned from" or similar **business-relevant** links (the Leader may mark which are mandatory at G0)
3. The **requirements page** of each mandatory linked Issue (via `get-confluence-url` or by parsing the description) → fetch it
4. Existing child pages under the current Issue hub (PRD, earlier design, earlier API contract)

| Role | Typical upstream reads |
| --- | --- |
| @ProductManager | scope boundaries of the linked Epic/Story; avoid duplicating ACs |
| @Architect | the linked requirement's design child page; extend vs rewrite |
| @BackendDev / @FrontendDev | the linked requirement's API contract / frontend impl spec; breaking-change diff |
| @Designer | linked design pages; component reuse |
| @Tester | the linked requirement's T1/T2 pages; **`MULTICA.md` §2 of every repo** for automation paths; regression scope |

### 2.3 What happens if you skip it

- Re-implementing something the linked requirement already shipped → G2/G3 FAIL
- Missing "depends on PROJ-100 shipping first" → that should have been flagged BLOCKED upstream
- A Reviewer can FAIL a deliverable purely for not citing the linked PRD / contract

### 2.4 Recommended commands

```bash
# Current Issue + link list
python multica-platform-jira/scripts/get_issue.py \
  --url "https://jira.../browse/PROJ-200" -o data/jira.json

# Include linked Issues' descriptions and links (one level)
python multica-platform-jira/scripts/get_issue.py \
  --url "https://jira.../browse/PROJ-200" --with-linked -o data/jira-full.json

# Read a linked PRD
python multica-platform-confluence/scripts/fetch_page_by_url.py \
  --url "<Confluence URL from the linked issue>"
```

### 2.5 What goes into Agent Instructions

Every producing role's instructions should contain:

```text
Before starting: get the current Issue key. If linked_issues exist, read the linked
issues and their design page bodies as directed by the Leader / Issue notes.
On conflict, the current Issue plus the latest revision record wins.
```

Details: `multica-platform-jira` → `references/upstream-read.md`.

---

## 3. Relationship to the flow and the gates

- **G0**: Leader confirms the multi-repo matrix + the list of mandatory linked Issues
- **G1**: Architect/Designer deliverables should cite the linked design (if this is an increment)
- **G2**: every repo's deploy branch + local unit-test evidence (backend); the comment carries all SHAs
- **G3**: Tester folds the linked requirement's regression items into the T2 supplement list
