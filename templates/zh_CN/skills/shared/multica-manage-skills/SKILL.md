---
name: multica-manage-skills
description: 查询已部署的 multica 平台 API，获取 workspace / agent 统计信息（agent 运行次数、30 天活动明细、各 workspace 汇总）。当用户需要查 multica 数据（如“每个 workspace 的 agent 运行次数”“workspace 统计”“multica 接口数据”），或访问 <MULTICA_API_URL> 的 API 信息时使用。脚本为纯标准库 Python，无需安装依赖。
---

# multica-manage-skills

## Overview

multica 是自部署的 agent 编排平台（线上地址 `<MULTICA_API_URL>`）。本 skill 提供一套可随时调用的 Python API 客户端，用于拉取 workspace 列表、每个 workspace 的 agent 列表、agent 30 天运行次数与日活明细，并输出汇总报表。

## 认证与配置

脚本通过 `Authorization: Bearer <token>` 认证，workspace 通过 `X-Workspace-Slug` 请求头指定（slug 或 UUID 均可）。

**本脚本不读取任何本地配置文件**（不读 `~/.multica/config.json`，也不读脚本目录下的 json），只接受命令行参数与环境变量，避免本地磁盘文件干扰。

token 解析优先级（从高到低）：
1. `--token` 参数
2. 环境变量 `MULTICA_API_TOKEN`

API 地址解析优先级（从高到低）：
1. `--url` 参数
2. 环境变量 `MULTICA_API_URL`
3. 默认 `<MULTICA_API_URL>`

> 推荐把 token 与地址放进环境变量，一劳永逸（PowerShell 持久化示例）：
> ```powershell
> [Environment]::SetEnvironmentVariable("MULTICA_API_TOKEN", "mul_xxx", "User")
> [Environment]::SetEnvironmentVariable("MULTICA_API_URL", "<MULTICA_API_URL>", "User")
> ```
> 新开终端后即生效。token 在 Web UI 的 Settings → Access Tokens 创建（形如 `mul_xxx`）。如果脚本报 401/403，优先检查 `MULTICA_API_TOKEN`。

## 快速开始

脚本位置：`{skill_base_dir}/scripts/multica_api.py`（用户级 skill，任何项目可用）。

```powershell
# 列出所有 workspace
python scripts/multica_api.py workspaces

# 某 workspace 的 agent 列表
python scripts/multica_api.py agents --workspace <workspace-slug>

# 某 workspace 每个 agent 的 30 天运行次数（JSON 输出）
python scripts/multica_api.py run-counts --workspace <workspace-slug> --json

# 某 workspace 每个 agent 的 30 天日活明细
python scripts/multica_api.py activity --workspace <workspace-slug>

# 所有 workspace 汇总统计
python scripts/multica_api.py report

# 单个 workspace 的 agent 级明细（合并运行次数+活动+名称）
python scripts/multica_api.py report --workspace <workspace-slug>

# 指定 token / 地址 / CSV 输出
python scripts/multica_api.py --token YOUR_API_TOKEN --url <MULTICA_API_URL> report --csv
```

## 命令一览

| 子命令 | 说明 | 必选参数 |
| --- | --- | --- |
| `me` | 当前登录用户信息 | 无 |
| `workspaces` | 当前用户可见的所有 workspace（id/name/slug/created_at） | 无 |
| `agents` | 某 workspace 的 agent 列表（id/name/runtime_mode） | `--workspace` |
| `run-counts` | 某 workspace 每个 agent 的 30 天运行次数 `[{agent_id, run_count}]` | `--workspace` |
| `activity` | 某 workspace 每个 agent 的 30 天日活 `[{agent_id, bucket_at, task_count, failed_count}]` | `--workspace` |
| `report` | 汇总：不带 `--workspace` 输出各 workspace 汇总；带 `--workspace` 输出该 workspace 的 agent 明细（含 fail_rate） | 可选 `--workspace` |

通用参数：`--url`、`--token`、`--workspace`、`--json`、`--csv`。

## 常见场景

1. **“统计每个 workspace 的 agent 运行次数”** → 跑 `report`（不带 `--workspace`），一行一个 workspace，含 agent 数、30 天总运行数、任务数、失败数。
2. **“某个 agent 最近运行情况”** → `run-counts --workspace <ws>` 拿运行次数，再 `activity --workspace <ws>` 看每日明细，用 `--json` 便于程序处理。
3. **想以 Python 模块方式集成** → `from multica_api import MulticaClient`，构造 `MulticaClient(base_url, token)` 后直接调用 `list_workspaces()` / `agent_run_counts(ws)` / `workspace_report(ws)` 等方法，异常统一抛 `MulticaError`。
4. **服务器不通/鉴权失败** → 脚本会打印 HTTP 状态码与响应体片段；401/403 时提示检查 token。

## 端点说明（详见 references/api_reference.md）

- `GET /api/me`、`GET /api/workspaces` 无需 workspace 头
- `GET /api/agents`、`GET /api/agent-run-counts`、`GET /api/agent-activity-30d` 需要 `X-Workspace-Slug`

## Resources

- `scripts/multica_api.py` — 上述 API 客户端 + CLI（纯标准库，可直接运行或 import）
- `references/api_reference.md` — 端点、请求头、响应结构说明（来自 multica 源码）

