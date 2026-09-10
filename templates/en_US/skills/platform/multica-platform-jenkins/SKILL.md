---
name: multica-platform-jenkins
description: Platform-layer skill (placeholder shell): read/write capability for CI/CD systems (Jenkins-class) — trigger parameterized builds, poll status, fetch console logs. Parameters are auto-discovered; never hardcode. Credentials injected via runtime env. Concrete CI URL / Job list in config.yaml, never in role prompts.
metadata:
  layer: platform
  replaces: any CI/CD system (Jenkins / GitLab CI / GitHub Actions / self-hosted pipeline / etc.)
  runtime:
    python: ">=3.10"
---

# Platform · Jenkins (placeholder shell)

> This is a **platform-layer placeholder shell**. The public multica-best-practices binds to no specific company's internal URLs or credentials.
> To onboard your own CI/CD system, only edit this skill's `config.yaml` and `scripts/`; all upstream orchestration skills stay untouched.

## Purpose

CI/CD system **read + write**: trigger Jobs, poll builds, fetch `consoleText`, return build URLs.

> **Parameter auto-discovery**: connect to the CI system API to read each Job's required parameters; Agents must not hardcode parameter names.

Default CI URL configured in `config.yaml` → `cicd.base_url` (placeholder: `http://<your-cicd-host>`).

## Agent standard flow (required)

```text
1. Resolve service (jobs-catalog / issue_service_map) + **deploy branch** (from the Issue source + affected ends, not feature; for linked Issues use the branch in the external system)
2. discover (required) — default copy from lastSuccessfulBuild, only override deploy branch
3. ready=false → fill missing params or BLOCKED ask human
4. trigger: multica-artifact-cicd-sync → trigger script
```

**Parameter priority**: `--param` > **branch hint** (branchName etc.) > **last SUCCESS build params** > CI default

## Files (suggested structure)

```text
multica-platform-jenkins/
├── SKILL.md
├── config.yaml
├── jobs-catalog.yaml     # per-env Job list (service → Job name)
├── .env.example
└── scripts/
    ├── trigger_env.py    # trigger by env + service
    ├── list_jobs.py      # list / query Jobs
    ├── cicd_cli.py       # low-level API
    └── lib/
```

## Install deps (once)

```bash
pip install -r scripts/requirements.txt
```

## List Jobs

```bash
python scripts/list_jobs.py --env dev
python scripts/list_jobs.py --env sit --service <service>
```

## Discover parameters (live from CI, per Job)

```bash
python scripts/cicd_cli.py discover-params --env sit --service <service> --branch release/<ISSUE>-<slug> --json
```

## Trigger build (auto-params by default)

```bash
python scripts/trigger_env.py --env sit --service <service> --branch release/<ISSUE>-<slug> --json
python scripts/trigger_env.py --env sit --service <service> --branch release/<ISSUE>-<slug> --param deployVersion=1.0.0_795 --json
```

## Credentials

| Variable | Description |
| --- | --- |
| `CICD_USER` / `CICD_PASSWORD` | CI account (runtime env, never in role prompts) |
| `CICD_TOKEN` | optional token |

## Success criteria

- script exit code `0`
- every build `result=SUCCESS`
- return build URL list

## Relationship to orchestration skill

| Orchestration skill | Calls |
| --- | --- |
| `multica-artifact-cicd-sync` | `trigger_cicd.py` → internally calls this skill's Python scripts |

## Why it works

Parameter discovery: different projects have different parameter names, so the Agent discovers then triggers, avoiding hardcoding branchName. Job names live in `jobs-catalog.yaml`. A swappable platform layer is the core of "copy-paste-run".
