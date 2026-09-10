---
name: multica-frontend-impl
description: 前端实现：读 JIRA/Confluence/架构/UI/API，注重交互与体验完成界面开发。用于 @FrontendDev 组件实现、状态与对接验证。
---

# Frontend Implementation

## Purpose

在已确认的设计与 Issue 范围内，把 **UI / 交互 / 体验** 落地为可用界面，并正确对接 API。

> 与 `multica-artifact-frontend` 分工：**frontend-impl 管怎么读上游、怎么写组件与体验；artifact-frontend 管实现说明文档规范与 Confluence 落地**。

## Platform 协作

| Platform skill | 本 skill 用途 |
| --- | --- |
| `multica-platform-jira` | 读 Issue / AC |
| `multica-platform-confluence` | 读 PRD / 设计 / API 契约 |
| `multica-platform-figma` | 读 UI 设计（Issue / Designer 链接） |

发布 impl-spec 走 `multica-artifact-frontend`；本 skill 不重复 REST 细节。

## 开工前：读上游（必做）

| 顺序 | 来源 | 方式 |
| --- | --- | --- |
| 1 | Issue / 验收标准 | `multica-platform-jira` → `jira_cli.py get-issue <KEY>` |
| 2 | PRD | JIRA → Confluence `fetch_page.py` |
| 3 | 架构设计 | Leader 派活或 JIRA 设计链接 → `fetch_page.py` |
| 4 | UI 设计 | @Designer `multica-design-ui-impl` 链接 |
| 5 | API 契约 | @BackendDev `multica-artifact-backend` Confluence 链接 |
| 6 | 现有前端代码 | 局部阅读 / codegraph |

契约或 UI 缺失 → **mock 先行**并记录 Mock 策略；接口语义不明 → **BLOCKED**，不发明 API。

## 体验优先流程（核心）

```text
1. 读 AC- / UI / 架构「实现步骤（前端）」→ 列出页面与状态机
2. 写/更新 impl-spec.md（交 multica-artifact-frontend 发布，可选但推荐）
3. 按状态实现：默认态 → 加载 → 空态 → 异常 → 无权限
4. 交互：即时反馈、防重复提交、错误可理解文案
5. 对接 API：严格按契约；错误分支与重试 UX 写进 impl-spec
6. 组件/交互测试 + 手动走查关键路径
7. 贴可复跑验证证据
```

**规则**：

- **交互与体验**与功能同等优先级：不能只做 happy path。
- 不改 API 契约；问题回 @BackendDev。
- 响应式 / 无障碍按项目基线；至少覆盖主流程键盘可操作。
- 不无关重构；判门由 Leader 复跑 `multica-verification`。

## 编码规则

1. 先读 UI 与契约再写组件。
2. 组件职责单一；复用设计系统。
3. 后端未就绪用 mock，契约就绪后切换并删除临时 mock。
4. 报告变更文件 + 命令 + 结果。

## 完成证据

- 前端实现说明 Confluence 链接（若已发布）
- 页面/组件代码 + 测试
- Mock 说明（若用过）
- 与 AC- / API-ID 追溯
- 已知问题

## 挂载顺序（@FrontendDev）

```text
multica-frontend-impl → multica-artifact-frontend
```

## 为什么有效

体验与状态完整度在前端最容易漏；impl-spec 挂 Confluence 需求树下，评审与测试可对照同一份说明。
