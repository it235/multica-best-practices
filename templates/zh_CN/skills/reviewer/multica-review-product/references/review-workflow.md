# PRD Review 执行流程

ProductReviewer 接到 Leader 派活后按本顺序执行。勾选项见 [`checklist.md`](checklist.md)；报告见 [`report-template.md`](report-template.md)。

## 1. 锁定材料

- 读 Leader 派活的 PRD 链接（`multica-artifact-req-sync` 回传）+ Issue 原文
- 可选读：原型、数据口径、依赖说明
- 必要时只读调用 `multica-platform-confluence` / `multica-platform-jira` 拉全文
- 可选调用 `团队知识库（可选）` 核对术语（**禁止规则扩写**）

## 2. 校验可读性

- PRD 全文可访问且与 Issue 目标一致
- 触发 BLOCKED 条件 → 停止，列缺失项，汇报 Leader

## 3. 三阶段审视（不可跳步）

1. **价值判断** — 问题真实性、ROI、分期、替代方案、KPI-/G-
2. **逻辑审视** — 目标→方案→验收、权限、主/异常流程、BR-、口径、范围、跨系统边界
3. **清晰度审视** — 模糊词、缺定义、图文冲突、OP-；产出 Q-001…

## 4. 分级与结论

- 问题归入 Must Fix / Suggest / Nit
- 有 Must Fix → **FAIL**
- 无 Must Fix 且审查完整 → **PASS**（可带 Suggest/Nit、残余 OP- 风险）
- 材料不足 → **BLOCKED**

## 5. 输出并汇报 Leader

- 按 report-template 输出完整报告
- **只汇报 Leader**；不 @ProductManager、不私信、不推进开发排期

## 6. 复审

- 对照上一轮 Must Fix 逐条核对
- 轮次 +1（仅 FAIL 复审计轮；BLOCKED 后补材料重审不计上一轮 FAIL）

## BLOCKED

遇以下情况输出 **BLOCKED**，列出缺失项，**不计入** 3 轮 FAIL：

| 条件 | 说明 |
| --- | --- |
| 无 PRD 链接或全文不可访问 | 无法读 Confluence/JIRA/正文 |
| Issue 与 PRD 目标明显不一致 | 审错文档 |
| 上游描述冲突 | JIRA / Confluence / Issue 口径矛盾，无法判断 |
| 缺 Story Key 或业务背景 | 无法做价值/范围判断且 Leader 未提供 |

BLOCKED 与 FAIL：FAIL = 材料足够且存在 Must Fix；BLOCKED = 尚不能可靠审查。
