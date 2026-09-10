# 上游读取规范（JIRA + 关联 Issue + Confluence）

所有 **产出角色**（PM / Architect / Designer / Frontend / Backend / Tester）开工前执行。

---

## 顺序（不可跳步）

| 步 | 动作 | 工具 |
| --- | --- | --- |
| 1 | 读 **当前 Issue** JSON | `get_issue.py` 或 `jira_cli.py get-issue` |
| 2 | 读 **`linked_issues`**；按 Issue「参考资料」或 Leader G0 标注筛选 **必读** 关联 | 同上；可选 `--with-linked` |
| 3 | 解析 **Issue Hub**（第一个 Confluence pageId） | `get-confluence-url` / `resolve-parent-page-id` |
| 4 | 读 PRD / 已有子页（设计、契约、T1/T2） | `multica-platform-confluence` `fetch_page.py` |
| 5 | 读描述中的 **Figma**（Designer/Tester/Frontend） | `multica-platform-figma` |
| 6 | 信息仍不足 | **BLOCKED** + 待确认项；**禁止猜测** |

---

## 关联 Issue 怎么算「必读」

默认 **必读**（除非 Issue 或 Leader 明确写「忽略」）：

- `Relates` / `关联` / `Clone` / `复制自`
- `Blocks` 的 **被阻塞方**（当前 Issue 被谁挡）
- Issue 描述或「参考资料」中 **点名** 的 KEY

可选读：

-  distant Epic（仅当 PM 未单独给 PRD 链接且 Leader 要求追溯 Epic）

---

## `--with-linked` 行为

```bash
python scripts/get_issue.py --url "<JIRA_URL>" --with-linked -o data/jira-full.json
```

输出除当前 Issue 外，增加 `linked_issues_detail[]`：每项含 `key`、`summary`、`description_text`、`links`（Confluence/Figma）。

**Agent 义务**：对 `linked_issues_detail` 中必读项，对其 `links.confluence[]` 逐条 `fetch_page`；在产出物「上游引用」节列出 KEY + 链接。

---

## 产出物中如何引用

| 产物 | 引用写法 |
| --- | --- |
| PRD | 「关联需求 PROJ-100：[链接]；本需求差异：…」 |
| 架构设计 | 「基于 PROJ-100 设计 §3 增量；不变部分见链接」 |
| API 契约 | 「继承 PROJ-100 API-ID x-y；本需求新增 API-ID …」 |
| T1/T2 | 「回归 PROJ-100 CASE-xxx；本需求新增 CASE-…」 |

---

## 与知识库（KB）的关系

`团队知识库（可选）` 仅 **Step 0.5 背景/术语**；**不能替代** 读关联 JIRA/Confluence 正文。KB 答案须在产出中标注「参考 KB，非 AC 来源」。

---

## 常见失败

| Bad | Better |
| --- | --- |
| 只看当前 Issue 标题就开始写代码 | get-issue + linked + Confluence 读全再动手 |
| 把关联 Story 的 AC 整段复制进当前 PRD | 写清继承 vs 新增 AC- |
| linked_issues 为空就认为无历史 | 仍读 Issue Hub 子页（可能有未 link 的手动 URL） |
