# CI/CD and Test Pipeline (methodology)

> This document describes the methodology behind **G2.5 (CI/CD deploy)** and **Tester three-phase (T1 / T2 / T3)** in the Squad pipeline. No concrete platform URL, Job name, or credential appears here — they live inside the `multica-platform-*` and `multica-artifact-*` placeholder shells; each team fills in its own internal network.

## 1. Stage overview

```text
G2 implementation PASS
  │ each end merges to deploy branch and pushes
  ▼
G2.5 CI/CD deploy (@DevOps, multica-artifact-cicd-sync)
  │ build & deploy to test env, return env URL
  ▼
G3 test acceptance (@Tester T3, multica-test-t3-ui-automation + multica-test-orchestration)
  │ run automation in the deploy env, produce test report
  ▼
Human acceptance (G4)
```

**Key link**: G2.5 is the hard pre-gate of G3. Without the deploy env URL, T3 must not start (never substitute local mock for deploy-env verification). @DevOps and @Tester are decoupled — deploy only produces the env, test execution only consumes it.

## 2. Tester three-phase

| Phase | Trigger | Output | Gate |
| --- | --- | --- | --- |
| **T1** feature cases | after design finalizes, in parallel with API contract | feature cases + design study (to team case platform) | Leader gates |
| **Parallel** API cases | after API contract ready, in parallel with frontend/backend impl | API test cases (for T3) | Leader gates |
| **T2** supplement + coverage | after G2 PASS, before T3 | case-supplement list + coverage assessment (not a report) | Leader gates |
| **T3** automation exec | **after G2.5 PASS** | automation log + test report (G3 input) | G3 (Leader reviews) |

T1 / T2 only write cases and assess; **T3 is the only execution phase** and binds to the real deploy env.

## 3. Deploy branch model

- The Squad declares one **deploy branch** at G0 (default `release/<ISSUE-KEY>-<slug>`); all implementation ends merge to it then push.
- @DevOps CI/CD **only honors the deploy branch**, never a feature branch.
- For multi-repo multi-service, every service shares the same deploy branch (don't guess a separate feature branch per frontend/backend).

## 4. Role split

| Role | Responsibility in the pipeline |
| --- | --- |
| @Leader | declare deploy branch; after G2 confirm each end merged & pushed; gate G2.5 and G3 |
| @DevOps | after G2 PASS + push, use `multica-artifact-cicd-sync` to trigger build/deploy, return env URL (no business code) |
| @Tester | T1/T2 write cases & assess; after G2.5, T3 runs automation in the deploy env |
| @FrontendDev / @BackendDev | implement and merge to deploy branch, provide changed-file list for T2 |

## 5. Degradation path without @DevOps / no CI

- When no triggerable CI/CD exists, **skip G2.5**; T3 degrades to local / manual verification + explicit "no CI/CD deploy" labeling. Evidence requirements are unchanged — still give env / execution method / output.
- This does not conflict with the gate system: G2.5 is a "hard gate when CI exists", not a mandatory step. See `gates-and-evidence.md`.

## 6. Why it works

1. **Deploy and test decoupled**: DevOps only produces the env, Tester only consumes it — avoids "self-test, self-deploy, self-claim success".
2. **T1/T2 shift left**: cases prepared during design / coding, ready at implementation completion, not thought up after code is done.
3. **G2.5 hard-links T3**: testing must be on the real deploy env, avoids "tested on the dev machine then claim acceptance".
4. **Platform swappable**: all internal details live in the `multica-platform-*` layer; this methodology and the public role prompts carry zero internal binding.

## 7. Relationship to the three-layer skill model

```text
Role prompt (content) ── "use multica-artifact-cicd-sync to trigger CI/CD"
        │
Orchestration multica-artifact-cicd-sync ── calls ──┐
        │                                           │
Platform multica-platform-jenkins ─────────────────┘ (only place with CI URL / Job name / credentials)
```

A team onboarding its own internal network only fills the platform shell's `config.yaml` and `scripts/`; the upstream layers stay untouched.
