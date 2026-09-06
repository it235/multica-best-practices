# T1 测试用例 — {ISSUE-KEY}

| 字段 | 值 |
| --- | --- |
| 创建者 | @Tester |
| 创建时间 | {YYYY-MM-DD} |
| 版本 | v1.0 |
| 状态 | 草稿 / 已审核 / 已导入 JIRA |
| JIRA | {ISSUE-KEY} |
| 上游 PRD | {Confluence PRD / Issue Hub 链接} |
| 上游设计 | {Figma / 设计链接，或 N/A} |
| API 契约 | {Confluence 契约链接，或 N/A} |

## 追溯矩阵

| AC- | 设计/页面 | CASE-ID | 优先级 | 自动化 |
| --- | --- | --- | --- | --- |
| AC-1 | | CASE-001 | P0 | UI e2e / Apifox / 手工 |

## 功能用例（正文 · Confluence 主副本）

> T1/T2 **不生成 XMind**；审核通过后 👤 口令再导出 XMind 导入 JIRA。

### CASE-001 — {标题}

| 字段 | 值 |
| --- | --- |
| 模块 | {module/path} |
| 优先级 | P0 / P1 / P2 |
| 前置条件 | |
| 权限 | |

**步骤与预期**（等长）：

| # | 步骤 | 预期结果 |
| --- | --- | --- |
| 1 | | |
| 2 | | |

**关联 AC-**：AC-1

---

### CASE-002 — {标题}

（同上结构，每条用例一节）

## 接口场景（Apifox · 不写 JIRA）

| 项 | 值 |
| --- | --- |
| 契约来源 | {Confluence api-contract 链接} |
| Apifox 项目 ID | |
| AI 分支 | ai/{ISSUE-KEY}-openapi-{date} |
| 已补 endpoint / 场景 | {path + scenario 摘要，或 N/A} |
| Git manifest | tests/api/{ISSUE-KEY}/manifest.json |

## UI 自动化规划（T2 起入库）

| CASE-ID | tests/e2e 文件 | 状态 |
| --- | --- | --- |
| CASE-001 | test_case_001.py | 待 T2 编写 / 已有 |

## 覆盖自查

- [ ] 正向主路径
- [ ] 边界与异常
- [ ] 权限/无权限态
- [ ] 空态（涉及时）
- [ ] 与 AC- 一一对应

**缺口说明**：（无则写「无」）

## 修订记录

| 版本 | 日期 | 说明 |
| --- | --- | --- |
| v1.0 | | 初稿 |
