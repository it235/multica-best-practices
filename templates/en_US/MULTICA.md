# MULTICA — Squad context for this repo

> **Copy this to the root of the product repo** (with split frontend/backend repos, **one copy per repo**).
> @Tester / @FrontendDev / @BackendDev / Leader: **read this before starting**. Paths come from this file — **never guess them**.

---

## 1. Repo identity

| Field | Fill in |
| --- | --- |
| **layout** | `monorepo` (frontend + backend in one repo) \| `frontend` \| `backend` \| `fullstack` \| `other` |
| **Service name** (CI `--service`) | <!-- e.g. acme-web; N/A for a library or something with no deployment --> |
| **Related repos** (when split) | <!-- frontend: acme-frontend → backend: acme-api --> |

---

## 2. Test automation paths (read before Tester writes scripts / T3 runs)

### 2.1 Paths in this repo (list only what actually exists)

| Type | Path | Note |
| --- | --- | --- |
| **UI E2E (Playwright)** | `tests/e2e/` | pytest + playwright; 1 CASE = 1 `test_*.py` |
| **API manifest** | `tests/api/` | one subdirectory per Issue: `tests/api/<ISSUE-KEY>/manifest.json` |
| **Unit tests** | <!-- e.g. `npm test` / `pytest tests/unit` --> | Backend / Frontend self-check; must be green at G2 |
| **Local case draft** (optional) | `docs/test/<ISSUE-KEY>/` | draft before publishing to the team platform; not required |

**Single repo (monorepo / fullstack)**: fill the table **completely** — UI + API + unit-test commands — so the Tester only needs this file.

**Split repos**:

- **Frontend repo** `MULTICA.md`: fill in `tests/e2e/` (the real path if it exists); if there is no API manifest write `N/A (see the backend repo's MULTICA.md)`
- **Backend repo** `MULTICA.md`: fill in `tests/api/` and the unit-test command; if there is no UI E2E write `N/A (see the frontend repo's MULTICA.md)`
- The Issue **repo matrix** must list every repo name; the Tester **reads one `MULTICA.md` per repo** in that matrix

### 2.2 API test platform (optional)

Git stores **an index, not the steps**.

| Field | Value |
| --- | --- |
| Default projectId | <!-- or "see the team registry" --> |
| Manifest path | see `tests/api/` above |

Scenario steps live on a branch in the API platform; the manifest records the branch / scenarioIds.

---

## 3. Build and verification commands (Leader G2 / CI, optional)

```text
install:   <!-- pnpm install / pip install -r ... -->
lint:      <!-- optional -->
unit_test: <!-- required; G2 evidence -->
build:     <!-- optional -->
e2e:       <!-- cd tests/e2e && pytest . -->
```

When the repo already has CI, the Leader **cites the CI verdict** at G2 instead of re-running (see `multica-verification`).

---

## 4. Branch conventions (aligned with the Issue deploy branch)

| Type | Naming |
| --- | --- |
| deploy branch | `release/<ISSUE-KEY>-<slug>` (same as the Issue) |
| feature branch | `feature/<ISSUE-KEY>-<side>-<slug>` |

Automation scripts run in T3 only **after** the feature branch has merged into the **deploy branch**.

---

## 5. Credentials (never commit them)

| Purpose | Environment variable |
| --- | --- |
| UI login | <!-- e.g. APP_UI_USERNAME / APP_UI_PASSWORD --> |
| API test platform | `API_TEST_TOKEN` (agent secret) |

`.env` is gitignored; `MULTICA.md` carries **variable names only**, never values.

---

## Why this file exists

- Automation paths differ per project; **the Issue matrix names repos, `MULTICA.md` owns the paths**.
- With split repos each side reads its own copy, so the Tester cannot put e2e into the backend repo or misplace the manifest.
- Missing file = **BLOCKED**: ask a human to fill it in before writing any automation.
