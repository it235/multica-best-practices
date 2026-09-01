---
name: multica-technical-design
description: 基于 PRD、验收标准与现有代码产出最小技术方案，并写入项目仓库固定路径。只要需要架构分析、影响评估、实现步骤或技术设计文档，就使用本 skill；仅支持本地文件，不依赖外部平台、凭据或网络。
metadata:
  mode: local-only
  output: artifacts/<issue-id>/technical-design.md
---

# Technical Design

## Purpose

基于 PRD（或 Issue）、验收标准与现有代码库，产出**最小可行**的技术设计，并落地为可 diff、可评审、可追溯的仓库文件。

本 skill 只支持本地路径：不访问外部平台，不读取凭据，不发网络请求，也不返回外部 URL。

## 输入

- Issue 标识，例如 `GOO-3`
- PRD / Issue 的仓库相对路径
- 代码仓库与基线版本
- 适用的 AC-、约束与明确非目标

输入不足时返回 BLOCKED 和缺失项，不猜测设计。

## Process

1. 按输入路径读取 PRD / Issue 与验收标准。
2. 检查当前实现，优先复用现有模式，不做无边界扫库。
3. 识别相关文件、模块、服务与依赖。
4. 确定最小可行改动，并明确非目标。
5. 给出前后端可执行步骤、验证计划和 RISK- 风险。
6. 写入 `artifacts/<issue-id>/technical-design.md`。
7. 确认文件完整且已纳入版本控制，向 Leader 只回传该仓库相对路径。

## Principles

```text
现有模式 > 新抽象
小改动   > 大重构
复用     > 新依赖
```

## Output（必须包含）

| 章节 | 内容 |
| --- | --- |
| 理解 | 系统当前行为与需求目标 |
| 建议改动 | 最小可行方案与非目标 |
| 受影响组件 | 文件 / 模块 / 服务 / 依赖 |
| 实现步骤 | 给 @FrontendDev / @BackendDev 的可执行步骤 |
| 验证计划 | 命令、检查项及 AC- 映射 |
| 风险与边界 | RISK- 编号、回滚点、待确认项 |

固定输出：

```text
artifacts/<issue-id>/technical-design.md
```

禁止返回本机绝对路径、包含 `..` 的路径或外部链接。更新同一 Issue 时覆盖同一路径；内容变化后，下游门禁失效并重跑。

## Handoff

```text
技术设计已写入 artifacts/<issue-id>/technical-design.md。
请按该仓库相对路径读取；版本：<commit-or-revision>。
```

如流程仍挂载 `multica-artifact-design-sync`，它只能校验或保持上述固定路径，不得上传或改写为外部引用。

## 常见失败

- 先写到 `docs/design/.../design.md` 再发布：产生双路径；直接写固定输出。
- 只在评论里贴方案：没有版本化产物；必须写入仓库。
- 回传平台 URL 或本机绝对路径：下游不可复现；只回传仓库相对路径。
- 为了“架构完整”扩大改动：回到适用 AC-，选择最小可行方案。

## 为什么有效

技术方案与代码在同一仓库、同一审查链中版本化，固定路径让下游无需平台账号或搜索即可读取，同时保留最小改动与独立门禁原则。
