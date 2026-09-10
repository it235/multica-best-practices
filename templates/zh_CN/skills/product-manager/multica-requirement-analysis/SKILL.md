---
name: multica-requirement-analysis
description: 产品经理需求规范：把 Issue/诉求结构化为带编号 PRD（G-/FR-/BR-/AC-/KPI-/OP-/RISK-）。含知识库背景检索；结构就绪后交 multica-artifact-req-sync 落地。
metadata:
  orchestrates:
    - 团队知识库（可选）
  origin:
    - multica-requirement-analysis
version: 2.0.0
---

# PM Requirement Spec（产品经理需求规范 · 内容）

## Purpose

把 Issue、会议结论、零散想法变成**清晰、可评审、可拆任务**的 PRD 内容（只管「写什么」，不管「落到哪个平台」）。

> 与 `multica-artifact-req-sync` 分工：**本 skill = 需求规范与编号；publish = Confluence / JIRA 创建与更新**。换平台只改 publish，不动本 skill。

## Platform 协作

| Platform skill | 本 skill 用途 |
| --- | --- |
| `团队知识库（可选）` | Step 0.5 查术语、历史需求背景（**参考**，不当新 AC） |
| `multica-platform-jira` / `multica-platform-confluence` | **不直接调用**；读写由 `multica-artifact-req-sync` 编排 |

智能体指令见 [`references/agent-instructions.md`](references/agent-instructions.md)。

## 两阶段（规范 ≠ 提交）

| 阶段 | 动作 | 停止点 |
| --- | --- | --- |
| **A 结构化** | 采集 + KB → 编号 PRD 草稿 | 交付 Markdown/HTML 草稿 + 修订记录 |
| **B 提交** | 用户/Leader 确认范围后 → `multica-artifact-req-sync` | 回传 Confluence + JIRA 链接 |

Review 后修订：回到阶段 A 改内容 → 再调 publish **更新**（非重复创建）。详见 publish skill Workflow B。

## Step 0.5 — 知识库（用法二分）

调用 `团队知识库（可选）` → `kb_ask.py`（禁止 SSH/curl）。

| 信息类型 | 能否写进 PRD | 写哪里 |
| --- | --- | --- |
| 术语、模块边界、历史背景 | **参考** | 背景/修订记录/OP- 引用 |
| 菜单路径、权限名、字段别名（当前需求相关） | **应当使用** | FR-/BR-/AC- 可执行描述 |
| 历史规则、他系统口径、当前需求未写的字段 | **禁止当新 FR/AC** | 仅背景；冲突以当前 Issue 为准 |

138 不可用：标注「知识库不可用」，**不阻断**结构化；禁止臆造业务规则。超时停轮见 platform KB SKILL。

## Process

1. 识别业务目标（G- + KPI-）
2. 用户角色 / 权限
3. 范围（含 / 不含）与非目标
4. 约束（兼容性 / 性能 / 安全 / 时间）
5. 验收标准（AC-，可测试）
6. 歧义 → OP- 待确认清单
7. 依赖与风险（RISK-）

## Requirement Structure

章节基线见 `multica-platform-confluence` 的 `scripts/templates/prd-template.md`：

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

正式 PRD 至少包含：一句话定义、背景、G-/KPI-、用户与权限、范围、FR-/BR-/AC-、字段口径、空态/异常态/无权限态、RISK-/OP-、**修订记录**。

## Output

- **目标（G-）**、**范围**、**非目标**
- **验收标准（AC-）**、**约束**、**依赖**
- **待确认项（OP-）**、**风险（RISK-）**
- **修订记录**：版本号、日期、变更摘要（Review 修订后必递增）

## Rule

歧义会实质影响实现 → **BLOCKED** → 说明缺什么、谁提供，只问 1 个最关键问题。

## Review 后修订（与 multica-review-product）

| Review 结论 | PM 动作 |
| --- | --- |
| **FAIL** | 按修改清单改 PRD 编号条目 → 更新修订记录 → `multica-artifact-req-sync` **Workflow B 更新** → 请 ProductReviewer 复审 |
| **PASS** | 交 Leader `multica-verification`；OP- 未关闭项仍不得进开发 |

ProductReviewer **只评不改**；PM 在用户/Leader 授权「按 review 修订」后执行修订。

## Handoff

```text
1. multica-requirement-analysis   — 结构化 PRD（本 skill）
2. multica-artifact-req-sync — Confluence + JIRA 创建/更新 + 可选钉钉
```

## 为什么有效

需求歧义在下游放大。编号 + OP- 清单 + KB 背景（不扩 scope）让 PRD 可评审、可测；内容与平台解耦，Review 后可二次更新而不重复建 Story。
