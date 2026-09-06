---
name: multica-technical-design
description: 基于 PRD 与现有代码产出最小技术方案。用于 @Architect 架构分析、影响评估、实现方案设计；含文档元数据与复审修订规范；草稿就绪后交 multica-artifact-design-sync 落地。
---

# Technical Design

## Purpose

基于 PRD（或 Issue）与现有代码库，产出**最小可行**的技术设计（只管「写什么」，不管「落到哪个平台」）。

> 与 `multica-artifact-design-sync` 分工：**technical-design 产出结构与内容；artifact-architect 校验产物并调用 Confluence/JIRA platform skills 落地**。  
> 与 `multica-review-architect` 配合：**初稿 → 评审 → 修订 → 复审**（最多 3 轮），每轮修订须递增版本并填写「评审回应」。

## Platform 协作

| Platform skill | 本 skill 用途 |
| --- | --- |
| `multica-platform-jira` / `multica-platform-confluence` | 读 PRD / Issue（开工前）；**写**由 `multica-artifact-design-sync` 编排 |

本 skill 只产出本地 `design.md`；凭据与发布 CLI 见 platform skill。

## Process

1. 读 PRD / Issue 与验收标准（AC-/FR-/BR-）。
2. 检查当前实现（优先 codegraph / 现有模式，不大面积扫库）。
3. 识别相关模块与现有模式。
4. 确定最小可行改动；**非目标**写清楚。
5. 识别数据/接口/非功能影响与依赖（RISK-、DECISION-）。
6. 定义验证方式（对齐 AC-）；填**需求追溯**表。
7. 写文档**头部元数据**（创建者、创建时间、版本、状态）。
8. 信息不足 → BLOCKED，写入「待决事项」，不猜。

## Principles

```text
现有模式 > 新抽象
小改动   > 大重构
复用     > 新依赖
可验证   > 不可验证的设想
可回滚   > 一次性不可逆改动
```

## 本地草稿路径

```text
docs/design/<ISSUE-KEY>/design.md
```

章节基线见 `multica-platform-confluence/scripts/templates/design-template.md`。

## 文档头部（必须，置于 H1 标题下）

设计正文**第一块**必须是元数据表，便于 ArchReviewer 追踪版本与责任人：

| 字段 | 规则 |
| --- | --- |
| **创建者** | `Architect-<member-id>`（与 Squad member 一致） |
| **创建时间** | `YYYY-MM-DD HH:mm`（团队约定时区，默认 UTC+8） |
| **版本** | 语义化 `v0.1` 起；**每次因评审修改递增**（v0.2、v0.3 …） |
| **状态** | `草稿` → `评审中` → `已通过`；废弃用 `已废弃` |
| **JIRA** | Issue Key |
| **上游 PRD** | Confluence 需求页链接（从 JIRA 解析，勿留空） |

示例：

```markdown
# 技术设计 — PROJ-1813 分片上传

| 字段 | 值 |
| --- | --- |
| **创建者** | Architect-u1024 |
| **创建时间** | 2026-08-26 15:30 |
| **版本** | v0.1 |
| **状态** | 草稿 |
| **JIRA** | PROJ-1813 |
| **上游 PRD** | http://confluence.../pages/viewpage.action?pageId=... |
```

## Output（必须包含）

| 章节 | 必填 | 内容 |
| --- | --- | --- |
| **文档头部** | 是 | 创建者、创建时间、版本、状态、JIRA、上游 PRD |
| **理解** | 是 | 系统当前做什么；与 PRD 范围对齐 |
| **非目标** | 是 | 明确不做的事，防范围蔓延 |
| **建议改动** | 是 | 最小可行方案；可选「方案备选与取舍」简述 |
| **受影响组件** | 是 | 文件 / 模块 / 服务 · 变更类型 · 说明 |
| **数据与状态** | 涉及时 | 实体/字段/状态变更；一致性要求 |
| **接口与契约边界** | 涉及时 | 前后端/UI 边界；错误与鉴权约定 |
| **实现步骤** | 是 | 给 @FrontendDev / @BackendDev 的可执行步骤 |
| **非功能需求** | 按需 | 性能、安全、可用性、可观测性对策 |
| **迁移与回滚** | 按需 | 数据迁移、功能开关、回滚步骤 |
| **验证计划** | 是 | 验证项 · 方式 · 对应 AC- |
| **需求追溯** | 是 | AC-/FR-/BR- → 设计决策 → 实现步骤 |
| **风险与边界** | 是 | RISK-n · 风险 · 缓解 |
| **待决事项** | 有则填 | DECISION-n；BLOCKED 项 |
| **评审回应** | 复审时 | 对照 ArchReviewer 修改清单逐条回应 |
| **修订记录** | 是 | 日期 · 版本 · 作者 · 变更摘要 |

## 架构师写作角度（易漏项）

设计评审常在这些角度被追问，初稿尽量覆盖：

| 角度 | 自检问题 |
| --- | --- |
| **范围** | 非目标是否写清？是否偷偷扩需求？ |
| **数据** | 谁写谁读？一致性/事务边界？历史数据怎么办？ |
| **并发与幂等** | 重复提交、竞态、重试是否考虑？ |
| **失败与降级** | 依赖挂了怎么办？部分失败可接受吗？ |
| **安全** | 鉴权、敏感数据、审计日志是否说明？ |
| **性能** | 量级假设？热点路径？是否需要异步/缓存？ |
| **可测试性** | 实现步骤能否对应到可执行的验证？ |
| **运维** | 部署顺序、配置项、监控告警、回滚？ |
| **跨端一致** | 与 UI/API 契约是否冲突？错误码/状态机是否统一？ |
| **追溯** | 每条 AC- 是否能在设计中找到落点？ |

## 复审修订流程（配合 multica-review-architect）

1. 读 Leader 转发的 **ArchReviewer 修改清单**（含阻断项 ID）。
2. **版本 +1**（如 v0.1 → v0.2），状态改 `评审中`。
3. 在 **评审回应** 表逐条填写：已修改 / 不采纳（须写理由）。
4. 更新受影响章节；**修订记录**追加一行。
5. 重新自检 → `multica-artifact-design-sync` → platform 发布（Confluence upsert 同 title 会更新版本）。
6. 通知 Leader 已修订，进入下一轮 ArchReviewer 复审（最多 3 轮）。

不采纳阻断项须 Leader 裁决，Architect 不得自行关闭评审。

## Handoff

```text
先用 multica-technical-design 写 docs/design/<ISSUE-KEY>/design.md（含头部元数据），
再用 multica-artifact-design-sync 自检后按 platform skill 发布并回传链接。
```

发布命令见 `multica-platform-confluence`（`publish_design.py --append-jira`）。

## 为什么有效

头部元数据 + 版本 + 评审回应，让多轮 ArchReviewer 评审可审计、可 diff；章节覆盖数据/非功能/追溯等角度，减少下游实现阶段返工。
