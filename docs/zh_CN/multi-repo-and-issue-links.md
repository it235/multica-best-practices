# 多仓库与 JIRA 关联需求

本文说明：**多仓需求**在 Squad / Multica 中如何识别与路由；**JIRA 关联 Issue** 各角色是否、如何读取上游内容。

---

## 1. 多仓库需求

### 1.1 Multica / Squad 能否自动识别？

**不能自动识别。** Multica 不会扫描 GitLab 组织或 JIRA 字段推断涉及哪些仓库。

**唯一事实来源**：Issue 模板中的 **仓库矩阵**（见 `templates/zh_CN/squad/*/issue.md` § Git 分支）。Leader G0 据此派活；DevOps 按矩阵逐仓触发 Jenkins。

### 1.2 Issue 中应写什么

| 字段 | 说明 |
| --- | --- |
| **仓库布局** | 同仓 / 分仓 / **多仓（≥2 个独立 repo）** |
| **仓库矩阵** | 每行：repo 名、Jenkins `--service`、**MULTICA.md**（根目录须有）、deploy/feature branch |
| **deploy branch** | 各仓 **同名**（默认 `release/<ISSUE-KEY>-<slug>`），CI 只认 deploy branch |
| **范围勾选** | 未勾选的端不派角色；某仓无改动则矩阵行标 **N/A** |

示例：

```markdown
| 仓库 | 服务 (Jenkins) | deploy branch | feature branch |
| --- | --- | --- | --- |
| acme-frontend | acme-web | release/PROJ-123-foo | feature/PROJ-123-frontend-foo |
| acme-api | acme-api | release/PROJ-123-foo | feature/PROJ-123-backend-foo |
| shared-lib | — | N/A（本需求不改） | — |
```

### 1.3 Leader / DevOps / 实现者分工

| 角色 | 多仓行为 |
| --- | --- |
| **Leader** | G0 核对矩阵完整；G2 要求 **每仓** 变更已 merge 到各自 deploy branch；评论贴各仓 SHA/MR |
| **FrontendDev / BackendDev** | 只在矩阵中属于自己的 repo 开发；不得猜测其它仓分支名 |
| **DevOps** | 对矩阵中每个需部署的行调用 `multica-artifact-cicd-sync` / Jenkins；回传 **各环境 URL** |
| **Tester T2/T3** | 从评论拼接 **全部** 仓的 SHA/MR；缺一则中断 |

### 1.4 常见失败

- Issue 只写「前后端分仓」但没有 repo 名 → DevOps 无法 `--service`
- 一仓 merge 了 deploy branch、另一仓仍在 feature → G2 不得 PASS
- 假设 Multica workspace 绑定多 repo 即可自动路由 → **错误**；须人类填 Issue 矩阵

---

## 2. JIRA 关联需求（Linked Issues）

### 2.1 平台能否读到？

`multica-platform-jira` 的 `get_issue.py` / `jira_cli.py get-issue` 输出含 **`linked_issues`** 数组（link 类型、方向、key、summary、status）。

可选 **`--with-linked`**：对每个关联 Issue 再拉一层描述与 Confluence/Figma 链接（用于「本需求是上一需求的迭代」）。

### 2.2 各角色是否必须读？

**是。** 开工前 **Read 上游** 须包含：

1. **当前 Issue** 描述 + 评论 + 附件  
2. **`linked_issues`** 中类型为 Relates / Blocks / 被 … 阻塞 / 复制自 等 **业务相关** 链接（Leader 可在 G0 标明哪些必读）  
3. 每个必读关联 Issue 的 **Confluence 需求页**（经 `get-confluence-url` 或描述解析）→ `fetch_page.py`  
4. 当前 Issue Hub 下已有子页（PRD、旧版设计、旧 API 契约）

| 角色 | 典型关联读法 |
| --- | --- |
| @ProductManager | 关联 Epic/Story 的范围边界；避免重复 AC |
| @Architect | 关联需求的架构设计子页；增量 vs 重写 |
| @BackendDev / @FrontendDev | 关联需求的 API 契约 / 前端 impl-spec；Breaking change 对比 |
| @Designer | 关联 Figma / 设计子页；组件复用 |
| @Tester | 关联需求的 T1/T2 Confluence 页；**各 repo MULTICA.md §2** 自动化路径；回归范围 |

### 2.3 不读关联内容的后果

- 重复实现已在关联需求交付的能力 → G2/G3 FAIL  
- 漏掉「依赖 PROJ-100 先上线」→ BLOCKED 应在上游就标出  
- Reviewer 可据「未引用关联 PRD/契约链接」判 FAIL

### 2.4 推荐命令

```bash
# 当前 Issue + 关联列表
python multica-platform-jira/scripts/get_issue.py \
  --url "https://jira.../browse/PROJ-200" -o data/jira.json

# 含关联 Issue 描述与链接（一层）
python multica-platform-jira/scripts/get_issue.py \
  --url "https://jira.../browse/PROJ-200" --with-linked -o data/jira-full.json

# 读关联 PRD
python multica-platform-confluence/scripts/fetch_page_by_url.py \
  --url "<来自 linked issue 的 Confluence URL>"
```

### 2.5 Agent 指令要点

所有产出角色的 Agent Instructions 应含：

```text
开工前：get-issue 当前 KEY；若有 linked_issues，按 Leader/Issue 备注读取关联 JIRA + 其 Confluence 链接正文；冲突以当前 Issue + 最新修订记录为准。
```

详见 `multica-platform-jira/references/upstream-read.md`。

---

## 3. 与 FLOW / 门禁的关系

- **G0**：Leader 确认多仓矩阵 + 必读关联 Issue 列表  
- **G1**：Architect/Designer 产物应引用关联设计（若增量）  
- **G2**：每仓 deploy branch + 本地单测证据（Backend）；评论含全部 SHA  
- **G3**：Tester 关联需求回归项纳入 T2 补充清单
