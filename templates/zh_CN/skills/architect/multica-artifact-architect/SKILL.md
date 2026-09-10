---
name: multica-artifact-architect
description: 架构师产物薄编排：校验设计草稿规范，落地时只调 multica-platform-confluence + multica-platform-jira。用于 @Architect 发布设计文档。
metadata:
  orchestrates:
    - multica-platform-confluence
    - multica-platform-jira
  local_draft: "docs/design/<ISSUE-KEY>/design.md"
---

# Artifact · Architect（薄编排）

## Purpose

**只规定架构师产物写什么、发布前怎么自检**；Confluence 上传、父页面解析、JIRA 回写全部由 platform skill 封装。

> 本 skill **不含脚本**；跨平台请直接调用 platform 层的 Python CLI（Windows / macOS / Linux 均可）。

## Platform 协作

| Platform skill | 本 skill 用途 |
| --- | --- |
| `multica-platform-jira` | 解析 Issue Hub（Confluence 需求页 pageId） |
| `multica-platform-confluence` | `publish_design.py` 发布 `design.md` |

凭据与 CLI 细节**只查 platform skill**。

## @Architect 标准流程

```text
1. multica-technical-design       — 写 docs/design/<ISSUE-KEY>/design.md
2. 自检（见下表）
3. multica-platform-confluence      — publish_design.py（默认父页面 = JIRA 需求 Confluence 页）
4. multica-platform-jira            — 已在 --append-jira 时一并回写；或单独 append-artifact-link
5. 向 Leader 回传 Confluence 链接
```

## 父页面规则（Issue Hub）

Issue 创建时已绑定 **JIRA 编号**；JIRA 描述中的 **Confluence 需求页** 是本需求的文档根（PRD Hub）。

| 规则 | 说明 |
| --- | --- |
| 默认父页面 | JIRA `get-confluence-url` 解析到的**第一个 pageId**（即 PRD/需求正文页） |
| 子页面 | 技术设计、后续 Confluence 文档产物均发布为该页的**子页面** |
| 回退 | JIRA 无 Confluence 链接时，用 `multica-platform-confluence/config.yaml` 的 `design_parent_page_id` |

Leader / 下游读 PRD：`multica-platform-jira` → `get-confluence-url` → `multica-platform-confluence` → `fetch-page`。

## 架构师产物规范（发布前自检）

本地草稿：`docs/design/<ISSUE-KEY>/design.md`（章节基线见 `multica-platform-confluence/scripts/templates/design-template.md`）。

| 章节 | 必填 | 内容要求 |
| --- | --- | --- |
| **文档头部** | 是 | 创建者、创建时间、版本、状态、JIRA、上游 PRD |
| **理解** | 是 | 与 PRD/Issue 对齐，不扩需求 |
| **非目标** | 是 | 明确不做的事 |
| **建议改动** | 是 | 最小可行方案 |
| **受影响组件** | 是 | 表：组件/文件/服务 · 变更类型 · 说明 |
| **数据与状态** | 涉及时 | 实体/字段/状态变更 |
| **接口与契约边界** | 涉及时 | 前后端/UI 边界 |
| **实现步骤** | 是 | 给 @FrontendDev / @BackendDev 的可执行步骤 |
| **验证计划** | 是 | 表：验证项 · 方式 · 对应 AC- |
| **需求追溯** | 是 | AC-/FR-/BR- → 设计决策 → 实现步骤 |
| **风险与边界** | 是 | 表：RISK-n · 风险 · 缓解 |
| **评审回应** | 复审时 | 对照 ArchReviewer REV-n 逐条回应 |
| **修订记录** | 是 | 日期 · 版本 · 作者 · 变更 |

自检 FAIL → 先补草稿，不调 platform。

## 落地（platform skill，一条命令）

```bash
pip install -r multica-platform-confluence/scripts/requirements.txt
python multica-platform-confluence/scripts/publish_design.py \
  <ISSUE-KEY> docs/design/<ISSUE-KEY>/design.md \
  --append-jira --json
```

- 默认从 JIRA 解析 Confluence 需求页作为父页面；需禁用：`--no-parent-from-jira`
- 显式指定父页面：`--parent <pageId>`
- JIRA 单独回写链接：`python multica-platform-jira/scripts/jira_cli.py append-artifact-link ...`

详细参数见 `multica-platform-confluence/SKILL.md` 与 `multica-platform-jira/SKILL.md`。

## 用法（角色侧）

```text
先用 multica-technical-design 写 docs/design/<ISSUE-KEY>/design.md，
再用 multica-artifact-architect 规范自检后，按 platform skill 发布并回传链接。
```

## 为什么有效

产物 skill 保持薄层：规范与流程在 artifact，能力与脚本在 platform；Issue 自带 JIRA + Confluence 需求链接，后续文档天然挂在同一需求树下，无需固定全局 pageId。
