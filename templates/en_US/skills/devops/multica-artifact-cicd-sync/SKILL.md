---
name: multica-artifact-cicd-sync
description: CI/CD artifact-orchestration skill (placeholder shell): after G2 PASS and code push, call the underlying CI/CD platform skill to trigger dev/sit builds, write back to the Issue, and return the deploy URL. Parameters auto-discovered from the CI API; the orchestration layer never hardcodes parameter names. Concrete platform in the multica-platform-* layer.
metadata:
  layer: orchestration
  orchestrates:
    - multica-platform-jenkins
    - multica-platform-jira
  runtime:
    python: ">=3.10"
---

# Artifact · CI/CD Sync (orchestration, placeholder shell)

## Purpose

After G2 PASS + push, call the underlying CI/CD platform skill to trigger build/deploy. **Parameters auto-discovered from the CI API**; the orchestration layer never hardcodes parameter names.

## Agent flow

```text
1. discover-only (recommended first, check missing):
   python scripts/trigger_cicd.py --issue <ISSUE-KEY> --env sit --branch release/<ISSUE-KEY>-<slug> --discover-only --json
2. trigger (**only the Issue deploy branch, never a feature branch**):
   python scripts/trigger_cicd.py --issue <ISSUE-KEY> --env sit --branch release/<ISSUE-KEY>-<slug> --json
3. missing params: append --param name=value
```

## Parameter resolution

Default (`use_last_success=true`):

1. Read all build params of `lastSuccessfulBuild`
2. **Only** replace branch-type params (branchName / branch / gitBranch …) with `--branch`
3. `--param` may override any item; `--no-last-success` disables this

---

## Workflow A: dev deploy

```bash
python scripts/trigger_cicd.py --issue <ISSUE-KEY> --env dev --service <service> --branch release/<ISSUE-KEY>-<slug> --json
```

## Workflow B: sit deploy (G2.5 → Tester T3)

```bash
python scripts/trigger_cicd.py --issue <ISSUE-KEY> --env sit --branch release/<ISSUE-KEY>-<slug> --json
```

Issue-prefix → logical-service mapping in `config.yaml` → `issue_service_map`, so `--service` is optional.

## Workflow C: multi-service

```bash
python scripts/trigger_cicd.py --env sit --service svc-a,svc-b --branch release/<ISSUE-KEY>-<slug> --json
```

## Usage (role side)

```text
After G2 PASS and code push, use multica-artifact-cicd-sync to trigger CI/CD and return the deploy link.
```

## Why it works

The orchestration layer depends only on the script; Issue-prefix auto-maps to the logical service in `jobs-catalog.yaml`. The underlying CI system (Jenkins / GitLab CI / GitHub Actions / etc.) is wrapped by the `multica-platform-*` layer, invisible to this skill.
