---
name: multica-backend-impl
description: 后端实现：读 JIRA/Confluence/架构设计，TDD 驱动 API 与服务端编码。用于 @BackendDev 契约先行、单元测试、集成验证。
---

# Backend Implementation

## Purpose

在已批准的技术设计与 Issue 范围内，**契约先行 + TDD** 完成后端实现。

> 与 `multica-artifact-api-sync` 分工：**backend-impl 管怎么读上游、怎么写代码与测试；artifact-backend 管 API 契约文档规范与 Confluence 落地**。

## Platform 协作

| Platform skill | 本 skill 用途 |
| --- | --- |
| `multica-platform-jira` | 读 Issue / AC（经 Issue Hub 或 JIRA URL） |
| `multica-platform-confluence` | 读 PRD / 架构设计（`fetch_page.py`） |

发布契约走 `multica-artifact-api-sync` → platform skill；本 skill 不直接写 REST。

## 开工前：读上游（必做）

| 顺序 | 来源 | 方式 |
| --- | --- | --- |
| 1 | Issue / 验收标准 | `multica-platform-jira` → `get-issue`；含 **`linked_issues`** |
| 2 | **关联 JIRA**（Relates/依赖等） | `get_issue.py --with-linked` → 必读关联的 Confluence/Figma（见 `upstream-read.md`） |
| 3 | PRD / 需求正文 | JIRA 解析 Confluence → `fetch_page.py` |
| 4 | 架构设计 | Leader 派活链接或 JIRA 描述中的设计链接 → `fetch_page.py` |
| 5 | 现有代码 | codegraph / 局部阅读，遵循项目约定 |

信息不足 → **BLOCKED**，写入待确认项，不猜接口形状。

## G2 前：单元测试（硬门禁）

**merge 到 deploy branch 之前**，必须在本地（或项目标准 dev 容器）跑通 **全部** 单元测试：

```text
1. 跑项目约定的 unit test 命令（如 mvn test / npm test / pytest tests/unit）
2. 必须 0 failure；既有测试不得因本次改动失败（无退步）
3. 新增/变更 API 须有对应单元测试（Red-Green-Refactor）
4. 失败 → 自行修复后再跑，直至全绿
5. 仅当本地无法跑（缺依赖/缺硬件）→ BLOCKED 列环境缺口，不得 push 后「等 CI 再看」
```

**禁止**：把单元测试失败留给 Jenkins/CICD 才发现；禁止为通过而删除或 skip 既有测试（除非 Architect/Leader 书面砍 scope）。

CI 是 **二次确认**，不是第一次跑单测的地方。

## TDD 流程（核心）

```text
1. 读 AC- / 架构「实现步骤（后端）」→ 列出 API-ID 与行为
2. 写/更新 api-contract.md（交 multica-artifact-api-sync 发布，供前端并行）
3. Red   — 写失败单元测试（业务逻辑、边界、异常）
4. Green — 最小实现使测试通过
5. Refactor — 保持测试绿，不扩 scope
6. 集成验证 — 跑项目约定命令，贴证据
```

**规则**：

- 业务逻辑须有**单元测试**；纯 CRUD 也需覆盖异常分支与边界。
- 先改契约文档再改实现；Breaking change 须升版本并知会 Leader / @FrontendDev。
- 不静默改字段名/语义；与 Architect 设计偏离须说明。

## 编码规则

1. 先读再改；遵循现有分层与命名。
2. 范围聚焦；不无关重构。
3. 错误处理：超时、幂等、并发按设计实现。
4. 报告**可复跑**的命令与结果。

## 完成证据

- API 契约 Confluence 链接（`multica-artifact-api-sync`）
- 变更文件列表
- **单元测试**：命令 + **全绿**结果（merge deploy branch **前**已跑通；0 failure、无测试退步）
- 集成测试（若项目要求）命令 + 结果
- 与 API-ID / AC- 的追溯说明
- 已知限制

## 挂载顺序（@BackendDev）

```text
multica-backend-impl → multica-artifact-api-sync
```

## 为什么有效

契约 + Confluence 文档让前端/T1 并行；TDD 把验收标准提前锁死在测试里，减少 G2 汇合返工。
