# PRD 审视报告模板

ProductReviewer 完成后按本模板输出，**汇报 Leader**。专业中文，术语保留英文（PRD、AC、FR、BR 等）；简短、可执行；不贴大段原文。

```markdown
## PRD 审视报告

**文档**：[名称 / Confluence 或 JIRA 链接]
**Issue**：[Multica Issue 或 Story Key]

**审视结论**：PASS / FAIL / BLOCKED
**价值判断**：值得做 / 不值得做 / 待判断
**逻辑判断**：逻辑闭环 / 有缺口 / 不自洽

### 1. 价值评估摘要
（3–5 条要点）

### 2. 逻辑闭环检查

| 检查项 | 结论 | 说明 |
| --- | --- | --- |
| 目标-方案-验收链路 | ✅ / ❌ / ⚠️ | |
| 角色与权限 | ✅ / ❌ / ⚠️ | |
| 主流程与异常流程 | ✅ / ❌ / ⚠️ | |
| 业务规则（BR-）一致性 | ✅ / ❌ / ⚠️ | |
| 数据口径 | ✅ / ❌ / ⚠️ | |
| 范围边界 | ✅ / ❌ / ⚠️ | |

### 3. 问题清单

| 编号 | 级别 | 类型 | 问题描述 | PRD 位置 | 建议 |
| --- | --- | --- | --- | --- | --- |
| Q-001 | Must Fix / Suggest / Nit | 价值/逻辑/清晰度 | | G-/FR-/AC- 或章节 | |

（Must Fix 对应 FAIL 阻断项；Suggest/Nit 非阻断）

### 4. OP- 与待确认项
- 阻塞开发的 OP-：…
- 非阻塞 OP-：…

### 5. 知识库/历史参考（若使用）
- 操作/术语核对：…
- 规则扩写检查：无 / 有（说明，**不**作为 PM 缺陷时写清）

### 6. 建议下一步
- FAIL：Leader 指派 @ProductManager spec 修订 → publish Workflow B → 复审
- PASS：汇报 Leader；**OP- 未关闭仍不得开发**；等待 multica-verification
- BLOCKED：列出需 Leader/人类补充的材料

### 7. 复审核对（复审轮次）
与上一轮 Must Fix：已解决 X 项 / 未解决 Y 项  
轮次：第 N / 3 轮（BLOCKED 不计 FAIL 轮次）
```

## PASS 时最低要求

即使 PASS，仍须填写：

- 已检查重点（价值/逻辑/清晰度各至少 1 条）
- 残余 Suggest 或 OP- 风险（无则写「无」）

## 禁止出现在报告中

- 「可进入开发 / 可排期」（专业评审 PASS ≠ G1）
- @ProductManager 或 member mention（由 Leader 派发）
- 创建/更新 JIRA、拆分 subtask
