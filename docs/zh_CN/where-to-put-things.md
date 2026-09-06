# 不知道某条指令该放哪？

> 这是本仓库最有价值的一页。记住它，胜过读 100 个 Prompt。

## 速查表

| 我想告诉 Agent…… | 放这里 |
| --- | --- |
| 「这次要做什么」 | Issue |
| 「这个项目有哪些背景」 | Project Instructions |
| 「你是什么角色」 | Agent Instructions |
| 「谁负责什么」 | Squad Instructions |
| 「各阶段产物放哪 / 下游怎么读」 | 由 `multica-artifact-*-sync` skill 落地到团队平台并回传稳定链接（见 [artifact-conventions](./artifact-conventions.md)） |
| 「某条能力该写成 Skill / 角色提示词 / 平台脚本」 | [role-skills-architecture](./role-skills-architecture.md)（四层模型） |
| 「平台 URL / 凭据 / REST 细节放哪」 | 只放 `multica-platform-*` 一层（见 [platform-collaboration](./platform-collaboration.md)） |
| 「完整流程怎么裁剪、谁先谁后」 | [FLOW](./FLOW.md)（交付物驱动，非角色流水线） |
| 「前后端分仓 / 多仓怎么路由」 | [multi-repo-and-issue-links](./multi-repo-and-issue-links.md) |
| 「自动化测试脚本放产品仓哪个目录」 | 目标仓库根目录的 `MULTICA.md`（见 [test-automation-in-repo](./test-automation-in-repo.md)） |
| 「怎么做某类检查」 | Skill |
| 「必须通过测试」 | CI（工程系统） |
| 「谁最终决定上线」 | Human |

## 心智模型

```text
Issue    ↓ 我们在做什么？
Project  ↓ 我们应该知道什么？
Agent    ↓ 我的职责是什么？
Squad    ↓ 谁应该做什么？
Skill    ↓ 我该怎么做？
CI / PR  ↓ 什么必须真的通过？
```

## 一句话版本

```text
Agent  = 角色（Role）
Skill  = 方法（Method）
Squad  = 协调（Coordination）
Issue  = 任务（Task）
CI     = 强制（Enforcement）
```

## 最常见的错误

把一切都塞进一个「全知全能」的 Agent Prompt：

```text
你是一个全能的软件开发专家，需要分析需求、设计架构、
写代码、测试、Review，并确保最终任务完成。
```

❌ 它同时占用了 Agent、Squad、Skill、Issue 四个位置。改任务、换团队、调流程时全部失效。

✅ 正确拆分：

- Agent Instructions：**我是谁**（负责实现已确认的方案）
- Squad Instructions：**谁做什么**（前端实现 → FrontendDev / 后端实现 + API 契约 → BackendDev（按 Issue 范围，缺失即跳过），判门 → Leader 用 multica-verification skill，业务评审 → Reviewer）
- Skill：**怎么做**（实现时的规则）
- Issue：**做什么**（这个任务的目标与验收标准）

## 配套

- 具体错误示范见 [`common-mistakes.md`](./common-mistakes.md)
- 如何裁剪与扩展见 [`adapt-and-scale.md`](./adapt-and-scale.md)
