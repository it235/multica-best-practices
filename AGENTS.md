# AGENTS.md

This repository is a practical **Copy. Paste. Run.** library of Agent · Squad · Skill · Issue templates for [Multica](https://github.com/multica-ai/multica). Every template can be copied and used as-is. Chinese is the source language of the content; this file is the agent entry point and is intentionally always in English (see the i18n convention below).

## Project structure

```text
README.md            Project entry: quick start / principles / structure (bilingual switcher)
AGENTS.md            Agent entry: project conventions and change rules (always English)
templates/           Everything copy-paste-ready (split by language)
├── zh_CN/           Chinese templates (default)
│   ├── MULTICA.md   Repo-context template: copy to the root of each product repo
│   │                (layout, test-automation paths, build/verify commands, branch conventions)
│   ├── agents/      Shared Agent Instructions (9 core + 6 optional *-reviewer for the reviewed Starter)
│   ├── skills/      Shared Skills (unified multica- prefix; see four-layer model)
│   │   ├── multica-gate-setup/  CI hard-gate templates ship inside this Skill
│   │   ├── multica-artifact-*-sync/  Orchestration skills landing content to team platforms (platform decoupled from roles)
│   │   └── multica-platform-*/  Platform-layer shells (Confluence/JIRA/Jenkins/Apifox/Figma) — only place holding company-specific URLs/credentials
│   └── squad/       Squad starters (copy the whole subdirectory and run)
│       ├── software-development/  Regular development (recommended)
│       ├── software-development-reviewed/  Same pipeline + dedicated Reviewers (two-layer gates)
│       └── bug-fix/               Minimal fix combination
└── en_US/           English templates (same structure as zh_CN/)
docs/                Methodology (split by language: zh_CN/ + en_US/)
├── FLOW.md                        Deliverable-driven flow, gate trimming, work-package table
├── role-skills-architecture.md    Why skills are layered and which layer a capability belongs to
├── platform-collaboration.md      Platform capability is written exactly once
├── test-automation-in-repo.md     Automation assets land in the product repo; paths come from MULTICA.md
└── multi-repo-and-issue-links.md  Multi-repo matrix routing + mandatory upstream reads
scripts/             Optional automation: push templates to a Multica workspace (Python 3.9+, stdlib only)
└── multica-sync/    Idempotent sync: import skills -> create/update agents -> create squad -> add members -> bind skills
SECURITY.md          Security check before sharing templates
```

## Core conventions

- **Skill naming**: `multica-` prefix + lowercase hyphenated; the `name` field in `SKILL.md` matches the directory name.
- **Skills mount by name**: documents reference `multica-xxx` (in backticks), never a repo path.
- **Agent naming**: `role + project + member-id` (e.g. `BackendDev-user-service-u1024`).
- **Automation is config-driven and secret-free**: `scripts/multica-sync/` holds optional sync scripts (Python 3.9+, stdlib only). They never contain a host, token, workspace or ID — those come from env vars or the git-ignored `config.local.json`; the join key is always the *name* (agent name, skill name, squad name), so no UUID is ever committed.
- **Directory semantics**: inside each language tree, `agents/` = roles, `skills/` = practices, `squad/` = squad combinations, and `docs/` = methodology. CI hard-gate templates live in the `multica-gate-setup` skill; artifact landing to team platforms lives in the six `multica-artifact-*-sync` skills (see `artifact-conventions.md` — platforms are decoupled from role prompts, swappable per company); there is no standalone `gates/` directory.
- **Four-layer skill model**: **content** (`multica-requirement-analysis`, `multica-technical-design`, `multica-backend-impl`, `multica-frontend-impl`, `multica-test-t1-design` / `-t2-coverage` / `-t3-*`) defines what "good" means; **orchestration** (`multica-artifact-*-sync`, `multica-test-orchestration`) lands artifacts and returns stable links; **platform** (`multica-platform-*`) is the only layer touching external systems; **review** (`multica-review-*`, plus `multica-verification` for gatekeeping) is executed by non-producers. Company-specific URLs/credentials live **only** in `multica-platform-*` shells. Public repo ships content + orchestration + platform shells; a team fills the shells' `config.yaml` / `scripts/` without touching roles. See `docs/zh_CN/role-skills-architecture.md`.
- **`MULTICA.md` per product repo**: automation paths differ per project, so the product repo (one copy per repo when frontend/backend are split) carries a root `MULTICA.md` declaring layout, test paths, build/verify commands, and branch conventions. Tester/FrontendDev/BackendDev read it instead of guessing; a missing file is BLOCKED. See `docs/zh_CN/test-automation-in-repo.md`.

## i18n convention (how Chinese and English coexist)

- **Source language is Chinese**: the Chinese tree is the source of truth.
- **Language directories**: `templates/` and `docs/` each contain a `zh_CN/` and an `en_US/` directory with the same file names (e.g. `docs/zh_CN/where-to-put-things.md` ↔ `docs/en_US/where-to-put-things.md`).
- **Root docs are single-file bilingual**: `README.md` / `README.en.md` each carry a switcher at the top; `CHANGELOG.md`, `ROADMAP.md`, `SECURITY.md`, `CONTRIBUTING.md` are single files written Chinese-first with English alongside.
- **One exception**: `AGENTS.md` is a single file, always English (the working language for agents). It has no Chinese mirror — agents read English directly.
- **Links are language-aware**: inside an English file, relative links point into `en_US/` trees; the Chinese tree is never moved or rewritten for translation purposes.
- **No build tooling**: this is a plain Markdown repo — do not add a docs generator or symlinks.
- **Machine files are not translated**: `LICENSE`, `*.yml`, `*.json`, `*.sh` (CI gate files are copied into both `zh_CN/` and `en_US/` skill directories).
- **Keep both in sync**: content changes to a Chinese file must be mirrored to its English counterpart in the same change (or explicitly tracked as pending in `CHANGELOG.md`).

## Change conventions

- **Repo-wide sync**: once a path, name, or structure diagram changes, sync README / Starter README / docs / ROADMAP, and grep the repo for stale names to confirm no residue (historical CHANGELOG entries excluded).
- **Record CHANGELOG**: every user-visible change appends an entry to `CHANGELOG.md` (version + date + Added / Changed / Removed).
- **Keep starters copy-paste-ready**: `templates/zh_CN/squad/software-development` is the MVP; changes must not break "copy → paste → run".
- **New templates come with explanation**: provide "why it works" and "common failure modes"; templates not yet proven on real tasks go to `ROADMAP.md` first.
- **Template style**: prefer directly copyable Markdown code blocks; agent templates state responsibilities / prohibitions / delivery format.

## Don't

- Commit secrets or sensitive information (tokens, API keys, private keys, local absolute paths, real workspace slugs / emails). Use placeholders (`YOUR_API_KEY`, `<workspace-slug>`).
- Claim there is a single "correct" number of agents — pick the smallest viable combination for the task.
- Replace the official Multica documentation — link to it instead.
- Introduce large binaries without good reason.
- Let completers approve their own work — gatekeeping is done by a non-producer (the Leader reruns `multica-verification` or relies on the CI verdict).

## How to work

1. `read_file` before editing.
2. Make minimal edits (`replace_in_file`); never rewrite whole files.
3. Confirm before destructive operations (delete, move, external publish).
4. After changes, grep for stale names/paths, run `read_lints`, and get zero errors.
