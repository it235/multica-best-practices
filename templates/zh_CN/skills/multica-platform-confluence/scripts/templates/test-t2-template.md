# T2 覆盖率评估 — {ISSUE-KEY}

| 字段 | 值 |
| --- | --- |
| 创建者 | @Tester |
| 创建时间 | {YYYY-MM-DD} |
| 版本 | v1.0 |
| JIRA | {ISSUE-KEY} |
| **T1 Confluence** | {t1-cases 链接 — 必填} |
| G2 证据 | {SHA / MR 链接} |
| API 契约 | {链接，或 N/A} |

## 结论

**评估完成 | 评估 BLOCKED** — {一句话}

> T2 只做静态缺口评估；**不生成 XMind**。

## AC 覆盖

| AC- | T1 CASE | 实现证据 | 状态 |
| --- | --- | --- | --- |
| AC-1 | CASE-001 | {文件/MR} | 已覆盖 / 假覆盖 / 缺口 |

## 用例补充（相对 T1 增量 · 正文）

### SUP-001 — create — {标题}

（结构同 T1 CASE：步骤/预期/AC-）

## Apifox 补充

| endpoint | 动作 | AI 分支 | 场景 ID |
| --- | --- | --- | --- |
| POST /api/... | 新增场景 | ai/... | |

## Git 自动化更新

| 类型 | 路径 | 说明 |
| --- | --- | --- |
| UI e2e | tests/e2e/test_{case_id}.py | 新增/修改 |
| API manifest | tests/api/{ISSUE-KEY}/manifest.json | scenarioIds 更新 |

## 回归风险

- …

## 修订记录

| 版本 | 日期 | 说明 |
| --- | --- | --- |
| v1.0 | | 初稿 |
