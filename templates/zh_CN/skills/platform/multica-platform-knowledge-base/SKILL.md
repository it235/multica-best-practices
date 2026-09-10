---
name: multica-platform-knowledge-base
description: 远程 Wiki 知识库问答（Knowledge Base Bridge（知识库 Bridge））。平台 skill，测试/前端/后端按需挂载；由内容 skill 按名调用。
metadata:
  credentials:
    optional:
      - KB_BRIDGE
---

# Platform · Knowledge Base（远程 Wiki）

## Purpose

通过 **Knowledge Base Bridge（知识库 Bridge）** HTTP API 查阅团队 Wiki 知识库。供 **@Tester / @FrontendDev / @BackendDev / @Architect** 查入口路径、术语、历史背景。

> 整合自 `内部知识库 squad`；脚本 `scripts/kb_ask.py`（仅 stdlib，跨平台）。

## 架构

```text
Agent（本机）
    ↓ kb_ask.py（HTTP）
Knowledge Base Bridge :3910
    ↓ Cursor SDK Agent + Skills
团队知识库
    /home/ubuntu/cursor-workspace/.cursor/skills/knowledge-base/知识库/
```

（路径在知识库服务侧；本机 Agent 仅通过 Bridge HTTP 访问。）

## Agent 执行规范（必须）

| 步骤 | 动作 | 禁止 |
| --- | --- | --- |
| 1 | `python scripts/kb_ask.py --health` | SSH 兜底、手写 curl |
| 2 | `python scripts/kb_ask.py "问题" [系统代码]` | 编造引用来源 |
| 3 | 呈现 stdout 的 `answer` | 把历史规则扩成当前验收点 |

## Bridge 识别规则

脚本自动满足 Wiki 问答条件（Agent **不得**改用其他 HTTP 方式绕过）：

- `taskId >= 500000000`（脚本默认生成）
- prompt 前缀 `【Wiki 知识库问答】`

## 何时使用

- 本机没有知识库副本，需查 CRM/MES/BOSS 等业务 Wiki
- 用户要求远程查 团队知识库
- **T1 Step 0.5b**：按模块关键词检索入口/术语/历史背景（验收仍以当前 JIRA 为准）

## 何时不必使用

- 本机已有完整知识库副本且可直接 Read/Grep 命中所需内容
- 问题与当前需求无关、或仅为验证 Bridge 连通性（用 `--health` 即可）

## 用法

```bash
python scripts/kb_ask.py --health
python scripts/kb_ask.py "CRM 病例管理入口在哪？"
python scripts/kb_ask.py "MES 工单状态" MES
python scripts/kb_ask.py "问题" --json
```

## 配置

| 变量 | 说明 |
| --- | --- |
| `KB_BRIDGE` | Bridge 地址，默认见 `config.yaml` |
| `KB_POLL_INTERVAL` | 轮询间隔秒，默认 2 |
| `KB_POLL_TIMEOUT` | 超时秒，默认 600 |

## 超时 / 不可用停轮规则（强制）

> 禁止为等知识库结果而卡在「运行中」。

1. `--health` 失败，或 `kb_ask.py` 超时/报错 → 标注「团队知识库不可用/超时」
2. **立刻结束本轮等待**，说明阻塞与可选方案（重试 / 跳过知识库 / 检查 Bridge）
3. 调用方（如 T1 Step 0.5）可标注后继续，**但不得**反复轮询到用户感知卡死
4. 禁止因不可用而臆造业务规则或引用来源

## 故障排查

| 现象 | 处理 |
| --- | --- |
| 无法连接 Bridge | VPN/内网；`python scripts/kb_ask.py --health` |
| 超时 | 按上方停轮规则；仅在用户明确要求时增大 `KB_POLL_TIMEOUT` |
| status=error | 加 `--json` 查看 `error` |

## 与测试流程的关系

- **T1 功能用例**（`multica-test-t1-design`）：生成前 Step 0.5 查知识库补入口/术语；**验收仍以当前 JIRA/PRD 为准**
- **接口场景补充**（`multica-platform-apifox`）：查同模块历史鉴权/造数方式
- **前端/后端实现**：查模块约定、错误码、权限语义

## 为什么有效

知识库从测试专用 squad 抽成 platform skill，各角色按名挂载，避免在角色提示词写死 Bridge 地址或 SSH 路径。
