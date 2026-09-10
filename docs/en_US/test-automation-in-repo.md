# Test automation assets in the repo

> T1/T2 case prose lives in **Confluence**; executable automation lives in **Git**.
> **Never guess paths** — read **`MULTICA.md`** at the root of the target repo (with split repos, read one copy per repo listed in the Issue matrix).

Template: [`templates/en_US/MULTICA.md`](../../templates/en_US/MULTICA.md) (copy it to the root of the product repo).

---

## 0. Path resolution (mandatory)

| Situation | What Tester / T3 must do |
| --- | --- |
| **Single repo** | Read that repo's `MULTICA.md` §2 — it must contain UI e2e, API manifest, and unit-test commands |
| **Frontend / backend split** | The Issue matrix lists the frontend repo + backend repo → **read `MULTICA.md` in each**; UI paths live only in the frontend repo, manifest / unit tests follow the backend repo (unless the frontend repo's `MULTICA.md` declares its own manifest) |
| **`MULTICA.md` missing** | **BLOCKED** — ask a human / DevOps to fill it in from the template before writing any automation |
| **Path differs from the skill default** | **`MULTICA.md` wins** (`tests/e2e/` in the skill is only a recommended default) |

---

## 1. Division of labour

| Asset | System of record | Git (path per `MULTICA.md`) |
| --- | --- | --- |
| T1/T2 **functional case prose** | Confluence | optional `docs/test/<ISSUE-KEY>/` draft |
| **Issue tracker** | Issue tracker | 👤 after the human go-ahead: XMind → import |
| **API automation** | API platform branch | `tests/api/<ISSUE-KEY>/manifest.json` (or the path `MULTICA.md` names) |
| **UI automation** | Git (Playwright) | `MULTICA.md` §2 `UI E2E` path (usually `tests/e2e/`) |

---

## 2. Directory example (single repo · must be written down in `MULTICA.md`)

```text
<product-repo>/
├── MULTICA.md                 # source of truth for paths
├── tests/
│   ├── e2e/                   # Playwright (MULTICA §2)
│   └── api/<ISSUE-KEY>/manifest.json
└── docs/test/<ISSUE-KEY>/     # optional draft
```

With split repos: the frontend repo usually only has `tests/e2e/`; the backend repo usually has `tests/api/` plus unit tests.

---

## 3. Phases and when assets land in the repo

| Phase | Confluence | API platform | Git (paths from `MULTICA.md`) |
| --- | --- | --- | --- |
| **T1** | full `t1-cases`; no XMind | add scenarios once the contract exists | optional manifest placeholder |
| **T2** | incremental `t2-coverage` | add scenarios per checklist | e2e skeleton + manifest → commit |
| **T3** | report pasted into the comment | run batch | run the e2e command from `MULTICA.md` against the deploy env; commit fixes |

---

## 4. `manifest.json` example

See `multica-test-orchestration` → `references/automation-assets-lifecycle.md`.

---

## 5. Relationship to gates

- **G2**: Leader runs `multica-verification` against the ACs + unit-test evidence (may cite CI — see `gates-and-evidence.md`)
- **G3**: T3 runs the **e2e** command from `MULTICA.md` + the API platform batch; professional sign-off comes from **TestReviewer** (reviewed Starter)

---

## 6. Common mistakes

| Bad | Better |
| --- | --- |
| Hard-coding `tests/e2e/` without reading `MULTICA.md` | Read `MULTICA.md` §2 of every repo first |
| Reading only one `MULTICA.md` with split repos | Read one copy per repo in the matrix |
| Keeping paths only in an Issue comment | Write them into `MULTICA.md` so they are reusable |
