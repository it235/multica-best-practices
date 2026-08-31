---
name: multica-technical-design
description: 基于 PRD 与现有代码产出最小技术方案。用于 @Architect 架构分析、影响评估、实现方案设计；草稿就绪后交 multica-artifact-design-sync 落地。
---

# Technical Design

## Purpose

基于 PRD（或 Issue）与现有代码库，产出**最小可行**的技术设计（只管「写什么」，不管「落到哪个平台」）。

> 与 `multica-artifact-design-sync` 分工：**technical-design 产出结构与内容；design-sync 调用 Confluence/JIRA platform skills 落地**。

## Process

1. 读 PRD / Issue 与验收标准（AC-）。
2. 检查当前实现（优先 codegraph / 现有模式，不大面积扫库）。
3. 识别相关模块与现有模式。
4. 确定最小可行改动（非目标写清楚）。
5. 识别依赖与风险（RISK-）。
6. 定义验证方式（对齐 AC-）。
7. 信息不足 → BLOCKED，不猜。

## Principles

```text
现有模式 > 新抽象
小改动   > 大重构
复用     > 新依赖
```

## 本地草稿路径

先写 Markdown 草稿，再交 design-sync 发布：

```text
docs/design/<ISSUE-KEY>/design.md
```

章节基线以本 skill 的内容规范为准。

## Output（必须包含）

| 章节 | 内容 |
| --- | --- |
| 理解 | 系统当前做什么 |
| 建议改动 | 最小可行方案 |
| 受影响组件 | 文件 / 模块 / 服务 |
| 实现步骤 | 给 @FrontendDev / @BackendDev 的可执行步骤 |
| 验证计划 | 如何验证，对应 AC- |
| 风险与边界 | RISK- 编号 |

## Handoff

草稿完成后，用 `multica-artifact-design-sync` skill：

```text
先用 multica-technical-design 写 docs/design/<ISSUE-KEY>/design.md，
再用 multica-artifact-design-sync 发布到 Confluence（父页面 <CONFLUENCE_DESIGN_PAGE_ID>）并回写 JIRA 链接。
```

Confluence 设计目录：[pageId=<CONFLUENCE_DESIGN_PAGE_ID>](http://<CONFLUENCE_URL>/pages/viewpage.action?pageId=<CONFLUENCE_DESIGN_PAGE_ID>)

## 为什么有效

设计先本地 Markdown、再 upsert Confluence，与 dev-workflow 一致：可 diff、可评审、链接稳定回写 JIRA，下游 @FrontendDev / @BackendDev / @Tester 靠链接消费。
