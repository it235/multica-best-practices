# PRD 提交工作流（创建 / 更新）

## 何时用哪条 Workflow

| 场景 | Workflow | 禁止 |
| --- | --- | --- |
| 首版 PRD 确认提交 | **A 创建** | — |
| Review FAIL 后修订 | **B 更新** | 重复 create-story |
| 仅改 OP- 状态、小补丁 | **B 更新** Confluence + JIRA 描述追加 | 新建页面替代旧链（除非 Leader 要求） |
| Confluence 不可用 | **E 降级**（全文进 JIRA 描述） | 静默丢 Confluence |

## Workflow A 检查清单

- [ ] PRD 含 G-/FR-/BR-/AC-/OP-/RISK- 与修订记录 v1
- [ ] Confluence 父页面 ID / space 已配置
- [ ] JIRA project Key 正确
- [ ] Story 描述含 Confluence 链接
- [ ] 回传 Leader：Confluence URL + JIRA Key

## Workflow B 检查清单（Review 后）

- [ ] 已读 ProductReviewer 修改清单，逐条处理或写入 OP-
- [ ] 修订记录版本号 +1，摘要写清「Review 第 N 轮修订」
- [ ] Confluence **update** 同一 pageId
- [ ] JIRA **同一** Issue Key 更新描述/append
- [ ] 未创建第二个 Story
- [ ] 请 ProductReviewer 复审（对照上一轮清单）

## 与 multica-review-product 闭环

```text
PM publish(A) → Review → FAIL → PM spec 修订 → publish(B) → Review 复审 → PASS → Leader verification
```

Review **PASS 不等于 G1 PASS** — 仍须 Leader 跑 `multica-verification`。
