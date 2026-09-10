---
name: multica-platform-apifox
description: Apifox 读写：OpenAPI 导入同步、接口打标、场景用例补充、T3 自动化跑批。平台 skill，测试/前端/后端共用；由产物编排 skill 按名调用。
metadata:
  credentials:
    priority:
      - APIFOX_ACCESS_TOKEN
  runtime:
    node: ">=18"
    external:
      - apifox-cli  # npm install -g apifox-cli
---

# Platform · Apifox

## Platform 协作

本 skill 为 **platform 层**；供 `multica-artifact-backend`、`multica-test-t1-design`、`multica-test-t3-api-automation` 等按名调用。凭据：`APIFOX_ACCESS_TOKEN`。

## Purpose

Apifox **读 + 写**统一能力，供 **@Tester / @BackendDev / @FrontendDev** 按名挂载：

| 能力 | 脚本 | 典型调用方 |
| --- | --- | --- |
| **OpenAPI 同步**（增/改/删 + 打标） | `scripts/sync_openapi.js` | @BackendDev 契约发布后 |
| **接口场景补充**（T1 并行） | `scripts/*.js`（见 `references/supplement-workflow.md`） | @Tester |
| **T3 自动化跑批** | `scripts/run_apifox.py` | @Tester（经 `multica-test-t3-api-automation`） |

> **跨平台**：Node 脚本 + Python runner；`npm install -g apifox-cli`。私有化基址见 `config.yaml` → `api_base_url`（默认 `https://apifox.example.com`）。

## Files

```text
multica-platform-apifox/
├── SKILL.md
├── config.yaml
├── .env.example
├── references/
│   ├── supplement-workflow.md
│   ├── reference.md
│   ├── agent-instructions.md
│   └── CHANGELOG.md
├── tests/                        # node --test tests/*.test.js
├── .apifox/
│   └── systems-registry.example.json
└── scripts/
    ├── sync_openapi.js           # OpenAPI 导入 + 打标 + 删 orphan
    ├── run_apifox.py             # T3 场景/套件跑批
    ├── lib/apifox.js             # CLI JSON 封装
    ├── systems-registry.js       # 系统名 ↔ projectId 登记
    ├── discover-auth.js
    ├── discover-scenario-target.js
    ├── generate-cases.js
    ├── append-to-scenario.js
    ├── safe-update-case.js
    └── validate-config.js
```

## 凭据

| 变量 | 说明 |
| --- | --- |
| `APIFOX_ACCESS_TOKEN` | Apifox CLI token（**禁止**写入 SKILL / Git） |
| `APIFOX_PROJECT_ID` | 当前项目数字 ID |
| `APIFOX_SOURCE_BRANCH` | 创建 AI 分支时的 **源分支**（默认 `main`），不是 sync 目标 |
| `APIFOX_BRANCH` | 本次写入的 **目标 AI 分支**（OpenAPI sync / 场景脚本必填） |
| `APIFOX_API_BASE_URL` | 私有化基址，覆盖 config |
| `APIFOX_OPERATOR` | 操作者简称（多人登记隔离） |

## Write · OpenAPI 同步（Backend / FE 契约）

Backend 发布 `openapi.json`（或从 `api-contract.md` 导出）后：

```bash
npm install -g apifox-cli
set APIFOX_ACCESS_TOKEN=<token>
set APIFOX_PROJECT_ID=<projectId>

node scripts/sync_openapi.js \
  --file docs/backend/<ISSUE-KEY>/openapi.json \
  --issue <ISSUE-KEY> \
  --tag <ISSUE-KEY> \
  --branch ai/<ISSUE-KEY>-openapi-<YYYYMMDD> \
  --json
```

**分支（强制）**：每次 OpenAPI 同步须 **新建** AI 分支，禁止直写 `main`。完整步骤见 [`references/openapi-branch-workflow.md`](references/openapi-branch-workflow.md)。

行为：

1. **导入** — `apifox import --format openapi`（增/改）
2. **打标** — 对 OpenAPI 内每条 path+method 匹配 endpoint，`endpoint update --tags` 追加 Issue tag
3. **删除** — 导出带该 tag 的 endpoint，与本次 OpenAPI 对比，多余者 `endpoint delete`（仅删带该 tag 的 orphan）

回传 JSON：`imported` / `tagged` / `deleted` / `errors`。

## Write · 接口场景补充（Tester T1 并行）

完整步骤见 `references/supplement-workflow.md`；断言/错误见 `reference.md`；Agent 指令见 `references/agent-instructions.md`。

回归测试：`node --test tests/*.test.js`（见 `tests/README.md`）。

要点：

- 任务卡片对齐 `projectId` / 环境 / 接口 / 写入意图
- `systems-registry.js lookup` 解析项目
- **禁止** patch 修改 `path/method/apiDetailId`
- 场景挂载：同一 endpoint 默认 **append-existing**，不重复建场景
- T3 跑批走 `run_apifox.py`，不在本 skill 出 PASS/FAIL 验收结论

## Run · T3 自动化

```bash
pip install -r scripts/requirements.txt
python scripts/run_apifox.py \
  --issue AAI-2466 \
  --base-url "https://sit.example.com" \
  --json
```

`multica-test-t3-api-automation` 薄编排调用本脚本；配置见 `config.yaml`（scenario / environment 映射）。

## Read

```bash
apifox endpoint list --project <id> --access-token <token>
apifox test-scenario list --project <id>
```

## 为什么有效

Apifox 能力从角色提示词剥离，测试/后端/前端共用同一 platform skill；OpenAPI 同步与用例补充分轨，避免 supplement 流程误改接口定义。
