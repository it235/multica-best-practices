# AC ↔ 设计追溯（T1 Step 1）

> 整合自 `ac-design-trace-squad`（原独立 skill）。写用例**之前**完成；追溯表写入 T1 生成报告的「设计追溯」节。

## 输入

- Issue / Jira 验收标准（优先带编号 AC-）
- Architect 设计：`docs/design/{KEY}/design.md` 或 Confluence 链接（经 `multica-platform-jira` + `multica-platform-confluence` 拉取）

缺设计：在报告标明「无设计，仅按 AC 生成」，不编造设计点。  
缺 AC 原文：BLOCKED 追溯口径，列出 Issue 仅有的一句话范围，仍可把设计 §验证方式列为「关注点（非 AC）」。

## 规则

- 验收分母只认当前 Issue/PRD AC；设计有、AC 无 → **只进关注点，不进验收**
- 冲突：Jira AC > 关联 PRD > 设计 > 知识库
- 操作信息（入口、权限名）可提供给用例步骤；规则不得扩写成新 AC

## 输出模板

```markdown
# 设计研读摘要 — {JIRA_KEY}

## 追溯表
| AC- | 设计章节 | 测试关注点 | 是否进入 T1 验收 |
|-----|----------|------------|------------------|
| AC-xx | §n | … | 是/否（否=仅关注） |

## 设计有但 AC 无（禁止写成验收点）
- …

## 风险/边界（供 T1/T2，非自动扩用例）
- …
```

## 为什么单独成节

用例生成前先锁定 AC 分母，避免把设计文档或知识库历史扩成额外验收点。
