# Platform Skill 协作约定

> 目的：**平台能力只写一份**（`multica-platform-*`）；角色 / 阶段 skill 只声明「读什么、写什么、调谁」，不重复 REST 与凭据说明。

## 1. 三层分工（与 artifact-conventions 一致）

```text
内容 / 阶段 skill     写什么、何时写（multica-test-t1-design、multica-technical-design …）
        ↓ 按名调用
platform skill          怎么读 / 怎么写 JIRA、Confluence、Apifox、Figma …
        ↓
团队平台 API            JIRA / Confluence / Apifox / Figma / Jenkins …
```

- **Agent Instructions 不写平台 URL、不写 REST 细节**；只写 skill 名称。
- **凭据优先级统一**：环境变量（`ATLASSIAN_USER` / `ATLASSIAN_PASS` 等）→ 角色 skill `.env` → 平台 skill `config.yaml`（见 `SECURITY.md`）。平台 skill 里**只留占位符**，真实值由使用方填。
- 每个会碰平台的 skill 在 frontmatter 声明 `metadata.orchestrates`（或 `metadata.uses_platform`），并在正文含 **「Platform 协作」** 一节。

## 2. 平台 skill 一览

| Platform skill | 读 | 写 |
| --- | --- | --- |
| `multica-platform-jira` | get-issue、get-confluence-url、resolve-parent-page-id | create-story、transition、append-description、append-artifact-link |
| `multica-platform-confluence` | fetch_page.py、fetch_page_by_url.py | publish_design.py、PRD HTML |
| `multica-platform-figma` | fetch_file.py | — |
| `multica-platform-apifox` | 场景 / 契约查询 | sync_openapi.js、场景补充、run_apifox.py |
| `multica-platform-jenkins` | 状态 / 日志 | trigger_env.py |

## 3. 角色 / 阶段 skill → 平台（标准矩阵）

| Skill | JIRA | Confluence | Figma | Apifox | Jenkins |
| --- | --- | --- | --- | --- | --- |
| `multica-artifact-req-sync` | 读写 | 读写 | — | — | — |
| `multica-artifact-design-sync` | 读 + 回写链接 | 读写 | — | — | — |
| `multica-artifact-api-sync` | 读 + 回写 | 读写 | — | 写（OpenAPI） | — |
| `multica-artifact-frontend` | 读 + 回写 | 读写 | 读（链接） | — | — |
| `multica-artifact-ui-sync` | — | 可选读 | 读 + 链接 | — | — |
| `multica-test-t1-design` | 读 | 读 + 写用例正文 | 读 | 写（场景） | — |
| `multica-test-t2-coverage` | —（材料来自 Issue 评论） | 读写增量 | — | 可选补场景 | — |
| `multica-test-t3-*` | — | 报告贴评论 | — | 跑批 | — |
| `multica-artifact-cicd-sync` | 可选读 Issue | — | — | — | 读写 |

## 4. Tester T1 fetch 迁移（已完成）

| 能力 | 实现 |
| --- | --- |
| 读 Issue、解析 Confluence/Figma 链接 | `multica-platform-jira` → `get_issue.py` / `jira_cli.py get-issue` |
| 读 Confluence 正文（URL、图片、子页） | `multica-platform-confluence` → `fetch_page_by_url.py` |
| 读 Figma | `multica-platform-figma` → `fetch_file.py` |
| 编排入口 | `multica-test-t1-design` → `fetch_all.py`（按 skill 名定位 platform 脚本） |

**不要**把用例 JSON 模板、覆盖清单并进 platform——那些留在 `multica-test-t1-design/references/`。

**不要**把「把用例批量导入测试管理平台」的脚本放进 platform——它绑定具体测试工具，留在团队自己的 T1 skill 里，且需人工口令后才跑。

## 5. SKILL.md 标准写法（复制块）

凡 `metadata.orchestrates` 非空的 skill，正文增加：

```markdown
## Platform 协作

| Platform skill | 本 skill 用途 |
| --- | --- |
| `multica-platform-jira` | … |
| `multica-platform-confluence` | … |

凭据与 CLI 细节**只查 platform skill**，本 skill 不重复维护。
```

内容 skill（如 `multica-backend-impl`）若只**间接**读上游，可写 `uses_platform: 经 artifact-* / Issue Hub` 或简短 Platform 协作表。

## 6. 常见错误

Bad: "在 test-t1-design 里再写一遍 JIRA Basic 认证步骤。"

Better: "Read `multica-platform-jira/SKILL.md`；T1 只写 fetch_all 的编排顺序。"

Bad: "Architect 和 Tester 各写一套 fetch Confluence。"

Better: "统一 `fetch_page_by_url.py`；Tester `fetch_all` 按 skill 名调 platform CLI。"
