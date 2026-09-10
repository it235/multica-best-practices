---
name: multica-review-product
description: 需求/PRD 专属评审框架。ProductReviewer 对 multica-pm-artifact-publish 提交的 PRD 做价值/逻辑/清晰度三阶段评审，输出 PASS/FAIL/BLOCKED 与 Must Fix/Suggest/Nit，汇报 Leader；FAIL 后 PM Workflow B 复审。
version: 1.1.0
---

# 需求（PRD）专业评审（ProductReviewer）

本 skill 提供对 **PRD / 需求产物** 的结构化专业评审。调用方为 `ProductReviewer`，评审对象为 `ProductManager` 经 `multica-pm-artifact-publish` 回传的 Confluence / JIRA 链接。

智能体指令见 [`references/agent-instructions.md`](references/agent-instructions.md)。  
执行顺序见 [`references/review-workflow.md`](references/review-workflow.md)。  
勾选项见 [`references/checklist.md`](references/checklist.md)。  
报告格式见 [`references/report-template.md`](references/report-template.md)。

## 什么时候用

- ProductReviewer 收到 Leader 派发的「评审 PRD」任务时
- PM 经 **Workflow B 更新** 后的**复审**轮次（对照上一轮 Must Fix 逐条核对）

## Platform 协作（可选、只读）

| Platform skill | 用途 |
| --- | --- |
| `团队知识库（可选）` | 核对术语、模块边界、历史背景（**参考**） |
| `multica-platform-confluence` / `multica-platform-jira` | Leader 未给全文时只读拉取 PRD（不创建/不改状态） |

**KB 用法二分（与 PM spec 一致）：**

- 可引用：术语、入口路径、权限名别名（核对 PRD 是否写清）
- **禁止**：把 KB/Confluence **历史规则**写成当前 PRD 的「应有 AC/FR」（规则扩写 → Must Fix 级误判，应标为参考差异而非 PM 缺陷）
- KB 不可用：标注「知识库不可用」，**不 BLOCKED**，继续审 PRD 正文

## 审视输入（缺则 BLOCKED）

| 必需 | 说明 |
| --- | --- |
| **PRD 全文** | Confluence/JIRA 链接或 Leader 提供的等价正文 |
| **需求上下文** | Issue、Story Key、业务背景（Leader 派活或 Issue 内） |

| 可选 | 说明 |
| --- | --- |
| 原型/Figma 链接 | 核对与文字 PRD 是否冲突 |
| 数据口径、依赖系统 | 跨系统/看板类需求 |

用例源与 PRD 都缺 → **BLOCKED**，列缺失项，汇报 Leader。

## 三阶段审视（严格顺序）

### 阶段 1：价值判断

评估是否值得在当前 scope 内推进（结论写入报告，**价值硬伤 → Must Fix → FAIL**）：

- 问题真实性：是否解决真实、紧迫的业务/用户问题
- 价值与 ROI：收益是否清晰、可衡量；投入产出是否合理
- 时机与优先级：范围是否应分期而非一次做大
- 替代方案：是否有更低成本路径（配置、运营、复用已有能力）
- 成功标准：**KPI-/G- 是否可验证**；缺失视为重大缺陷

阶段摘要：**值得做 / 不值得做 / 待补充信息后判断**（后两者通常对应 FAIL 或 BLOCKED）

### 阶段 2：逻辑审视（价值可讨论或值得做时执行）

- 目标 → 方案 → 验收 链路完整、前后一致
- 用户角色与权限：全场景覆盖；无越权/缺权限路径
- 主流程 + 异常 + 边界：空态、错误态、无权限态
- **BR-** 无矛盾；状态机/流转闭合
- 字段/数据口径：分子分母、数据源、刷新频率
- 依赖与假设显式；**范围与非范围**清晰；跨系统/API 责任方清楚

阶段摘要：**逻辑闭环 / 逻辑有缺口 / 逻辑不自洽**

### 阶段 3：清晰度审视（贯穿全文）

无法让设计/开发/测试直接执行的点，编号 **Q-001、Q-002…**（类型：价值/逻辑/清晰度）：

- 模糊词：适当、优化、等相关、等等、视情况、体验好
- 缺 AC- 的功能描述；缺字段/状态/权限定义
- 原型与文字 PRD 冲突且未说明以谁为准
- OP- 散落各处、无 Owner 或阻塞开发未标注

## 结论模型

| 结论 | 含义 | 对 Leader |
| --- | --- | --- |
| **PASS** | 无 Must Fix；可有 Suggest/Nit | 专业评审通过；仍须 verification；OP- 未关不得开发 |
| **FAIL** | 存在 Must Fix（含价值硬伤、逻辑缺口、清晰度阻断） | 指派 PM：`multica-pm-requirement-spec` 修订 → `multica-pm-artifact-publish` Workflow B → 复审 |
| **BLOCKED** | 材料不足或上下文冲突，无法可靠审查 | 补材料后再派；**不计** 3 轮 FAIL |

BLOCKED 条件见 [`references/review-workflow.md`](references/review-workflow.md#blocked)。

## 问题分级

| 级别 | 说明 |
| --- | --- |
| **Must Fix** | FAIL 阻断；价值硬伤、逻辑不自洽、AC 不可测、阻塞开发的 OP- |
| **Suggest** | 可维护性、更清晰表述、更稳边界 |
| **Nit** | 措辞、格式；可标注「可忽略」 |

每条须含：**问题** / **影响** / **建议** / **PRD 位置**（章节或 G-/FR-/BR-/AC-/OP- 编号）。

## 输出

使用 [`references/report-template.md`](references/report-template.md) 模板。简要头：

```text
【PRD 评审】<链接>
结论：PASS / FAIL / BLOCKED
价值判断：值得做 / 不值得做 / 待判断
逻辑判断：逻辑闭环 / 有缺口 / 不自洽
Must Fix / Suggest / Nit / Q- 清单 …
轮次：第 N / 3 轮（BLOCKED 不计 FAIL 轮次）
```

## Review 后修订闭环（与 PM 分工）

| 结论 | ProductReviewer | ProductManager |
| --- | --- | --- |
| **FAIL** | 输出 Must Fix；**不改 PRD** | Leader 指派：spec 修订 → publish **Workflow B** → 请求复审 |
| **PASS** | 汇报 Leader | OP- 未关闭仍不得进开发 |
| **BLOCKED** | 列缺失项 | Leader/人类补材料 |

**PASS ≠ G1 通过。** 不自行通知下游、不创建/更新 JIRA/Confluence、不 @ 其他 Agent。

## 审查原则

- 先读全文，再下结论；禁止只看标题或摘要
- 每个问题可追溯到 PRD 原文位置
- 不为了友善而通过有硬伤的需求
- 无明确证据时标「风险/疑问」，不断言必错
- PASS 时仍写已查重点与残余 OP-/Suggest 风险

## 边界

- 只评 PRD/需求，不评设计、代码、测试、UI
- 不替代 Leader 的 `multica-verification`
- 技术可行性交 ArchReviewer
- 第 3 轮仍 FAIL → 标注「升级人类」，交 Leader
