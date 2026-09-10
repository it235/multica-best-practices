---
name: multica-review-frontend
description: 前端实现专属评审框架。由 FrontendReviewer 调用，对 FrontendDev 产出做专业分析（UI/API 吻合、边界态、类型与模式、共享影响、单测），输出 PASS/FAIL/BLOCKED 与 Must Fix/Suggest/Nit 清单，汇报 Leader。
version: 1.1.0
---

# 前端实现专业评审（FrontendReviewer）

本 skill 提供对 **前端实现产物** 的结构化专业评审框架。调用方为 `FrontendReviewer`，评审对象为 `FrontendDev` 经 `multica-artifact-frontend` 回传的 Confluence 链接、变更文件列表，以及 Leader 派活时的 UI / API 链接。

智能体指令见 [`references/agent-instructions.md`](references/agent-instructions.md)。  
执行顺序见 [`references/review-workflow.md`](references/review-workflow.md)。  
逐项勾选项见 [`references/checklist.md`](references/checklist.md)。

## 什么时候用

- FrontendReviewer 收到 Leader 派发的「评审前端实现」任务时。
- 实现修改后进入复审轮次（对照上一轮 Must Fix 逐条核对）。

## 审查标准优先级

1. Issue / PRD 的 **AC-** 与用户目标
2. impl-spec、UI 设计、API 契约（Leader 派活链接）
3. **项目既有模式**（组件封装、hooks、store、api client、目录规范）— 有则优先于个人偏好
4. 本 skill checklist 中的通用前端质量项

## 结论模型

| 结论 | 含义 | 对 Leader |
| --- | --- | --- |
| **PASS** | 无 Must Fix；可带 Suggest / Nit | 专业评审通过，等通用门禁 |
| **FAIL** | 存在 Must Fix | 指派 @FrontendDev 修改后复审 |
| **BLOCKED** | 材料不足或上下文冲突，无法可靠审查 | 补材料后再派；**不计入** 3 轮 FAIL 计数 |

BLOCKED 条件见 [`references/review-workflow.md`](references/review-workflow.md#blocked-先停再判)。

## 问题分级

| 级别 | 映射 | 说明 |
| --- | --- | --- |
| **Must Fix** | FAIL 阻断项 | 功能缺陷、权限错误、契约偏差、严重类型/性能、用户流程不可用 |
| **Suggest** | 建议项 | 可维护性、更稳边界、更符合项目模式的写法 |
| **Nit** | 非阻断 | 命名、格式、轻微风格；Reviewer 可标注「可忽略」 |

每条尽量包含：**问题** / **影响** / **建议改法** / **文件或位置**。无明确证据时标为**风险或疑问**，不断言必错。

## 评审维度（逐项给结论）

1. **需求与 AC**：是否满足 issue 用户目标与每条 AC-
2. **UI 吻合度**：布局、交互、视觉状态是否对齐 Designer 产出
3. **交互与状态完整度**：loading / empty / error / disabled / permission / responsive
4. **API 契约吻合度**：参数、返回、错误分支、重试 UX 是否对齐契约
5. **类型与组件边界**：TS 清晰、Props/Emits 明确；避免组件内直接 HTTP
6. **项目模式一致性**：复用既有封装；无无关重构、无扩大改动范围
7. **影响面**：共享组件、路由、权限、缓存、核心流程
8. **测试与验证**：关键路径覆盖；实现者验证说明是否可信

## 输出格式

```text
【前端实现评审】<变更链接或 diff 范围>
结论：PASS / FAIL / BLOCKED
BLOCKED 原因（BLOCKED 时必填）：
- ...

Must Fix（FAIL 时必填；每项含 问题 / 影响 / 改法 / 位置）：
- ...

Suggest：
- ...

Nit（可标注「可忽略」）：
- ...

已运行的检查或测试：
- ...（无法运行时说明原因）

剩余风险或无法验证项：
- ...

PASS 时亦须填写：已检查重点 + 测试缺口或残余风险（若无则写「无」）

与上一轮 Must Fix 核对（复审时）：已解决 X 项 / 未解决 Y 项
轮次：第 N / 3 轮（BLOCKED 不计入 FAIL 轮次）
```

结论与清单**汇报给 Leader**，不自行改代码、不自行通知 FrontendDev。

## 审查原则

- 优先指出影响用户行为、交付质量或后续维护的风险。
- 不因个人偏好要求无意义改动；不要求无关重构。
- 不说空泛「建议优化」，必须说明原因和方向。
- 实现合理且无阻塞问题时，明确写出「未发现 Must Fix」。
- 缺少测试或无法验证时，写入剩余风险，而非默认 PASS。

## 边界

- 只评前端实现与相关单测，不评架构、需求、UI 设计稿本身、后端、测试用例集。
- 不替代 Leader 的通用门禁（`multica-verification` skill）。
- 第 3 轮仍 FAIL → 标注「升级人类」，交 Leader 处理，停止循环。
