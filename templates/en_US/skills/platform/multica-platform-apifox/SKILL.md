---
name: multica-platform-apifox
description: Apifox integration—read API contracts/scenarios, and run/supplement test scenarios. Credentials and CLI are only looked up here.
version: 1.1.0
metadata:
  scripts:
    - scripts/run_scenarios.py
    - scripts/fetch_contract.py
  externals:
    - apifox-cli
---

# Apifox Platform

## Responsibility
Integrate Apifox: read API contracts/scenarios, run test scenarios, and (during T1) supplement scenarios by contract. All Apifox credentials and the `apifox-cli` tool are only looked up here.

## Capabilities
- `fetch_contract.py`: pull API contract (OAS/Apifox) by project/environment.
- `run_scenarios.py`: run scenario IDs against a deployed environment, return logs/assertions.

## Usage (Tester)
- T1: supplement scenarios by contract (AI branch) → record in Confluence + manifest (MULTICA.md §2).
- T3: `run_scenarios.py --project-id <id> --environment-id <id> --scenario-ids <ids> --deploy-url <url>` → join overall verdict.

## Credentials
- `APIFOX_TOKEN` / project credentials via environment variables or Secret; see `scripts/run_scenarios.py --help`.
- Never hardcode tokens in skill content.
