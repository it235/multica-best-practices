---
name: multica-requirement-analysis
description: 把 Issue / 诉求结构化为带编号的 PRD 内容。用于 @ProductManager 需求澄清、范围确认、验收标准定义；结构就绪后交 multica-artifact-req-sync 落地。
---

# Requirement Analysis

## Purpose

把 Issue、会议结论、零散想法变成**清晰、可评审、可拆任务**的 PRD 内容（只管「写什么」，不管「落到哪个平台」）。

> 本 skill 与 `multica-artifact-req-sync` 分工：**analysis 产出结构与编号；req-sync 负责 Confluence / JIRA / 钉钉等平台对接**。换平台只改 req-sync，不动本 skill。

## Process

1. 识别业务目标（G- + KPI-）。
2. 识别预期行为与用户角色 / 权限。
3. 识别明确的范围（含 / 不含）。
4. 识别非目标。
5. 识别约束（兼容性 / 性能 / 安全 / 时间）。
6. 识别验收标准（AC-，可测试）。
7. 识别歧义 → 写入 OP- 待确认清单，不装作已确认。
8. 识别依赖与风险（RISK-）。

## Requirement Structure

把输入结构化为 PRD 章节，并叠加 Multica 编号：

| 章节 | 编号 |
| --- | --- |
| 一句话定义、背景 | — |
| 目标与成功标准 | G- + KPI- |
| 用户故事 | U- |
| 功能需求 | FR- |
| 业务规则 | BR- |
| 验收标准 | AC- |
| 待确认项 | OP- |
| 风险项 | RISK- |

正式 PRD 至少包含（详见 @ProductManager 角色指令）：一句话定义、背景、目标 G- + KPI-、用户与权限、范围、FR-/BR-/AC-、字段口径、空态 / 异常态 / 无权限态、RISK-/OP-、修订记录。

## Output

- **目标（G-）**：要解决什么问题
- **范围**：要改什么
- **非目标**：明确不改什么
- **验收标准（AC-）**：可测试的检查项
- **约束**：兼容性 / 性能 / 安全 / 时间
- **依赖**：前置条件
- **待确认项（OP-）**：集中维护，未关闭不得进开发
- **风险（RISK-）**：需关注的风险

## Rule

不要默默消化有歧义的需求。

如果歧义会实质影响实现：

→ BLOCKED  
→ 说明缺什么、谁提供，只问 1 个最关键问题。

## Handoff

结构就绪后，用 `multica-artifact-req-sync` skill 落地到团队需求平台（Confluence 页面 + JIRA Story + 可选钉钉），并回传稳定链接给 Leader。

> @ProductManager：「先用 `multica-requirement-analysis` 结构化 PRD，再用 `multica-artifact-req-sync` 落地并回传链接。」

## 为什么有效

需求阶段的歧义会在后续每个阶段被放大。用 BLOCKED 挡住歧义、用编号让下游可拆任务，比让 5 个 Agent 各自猜一遍便宜得多；内容与平台解耦后，换 Confluence / 语雀 / 飞书也不动分析逻辑。
