# Skills 索引（zh_CN）

本目录收录可直接挂载到 [Multica](https://github.com/multica-ai/multica) 的共享 Skill。每个子目录即一个 Skill，`SKILL.md` 是给 Agent 读的技能说明；带脚本的 Skill 另附 `README.md` 给出人类视角的快速上手。

## 一、平台层（Platform，含公司基建 URL / 凭据的占位外壳）

| Skill | 用途 | 主要入口 |
|---|---|---|
| `multica-artifact-*-sync` | 六类产物写入 `artifacts/<issue-id>/` 固定路径 | 各 skill 的 `SKILL.md` |

> 平台层只放"公司专属 URL / 凭据"的占位外壳，不含任何真实地址。使用方在 `.env` 填自己的 `JENKINS_URL` / `JIRA_URL` / `CONFLUENCE_URL` 等即可。

## 二、编排层（Orchestration，调用平台层把产物落地到团队平台）

| Skill | 用途 | 主要入口 |
|---|---|---|
| `multica-artifact-req-sync` | PRD / 需求 → Confluence + JIRA issue | `scripts/publish-prd.sh` |
| `multica-artifact-cicd-sync` | 代码评审结论 → 触发 Jenkins CICD | `scripts/trigger_cicd.py` |
| `multica-artifact-api-sync` | API 文档 → 团队 API 平台 | （纯编排） |
| `multica-artifact-design-sync` | 设计文档 → 团队设计平台 | （纯编排） |
| `multica-artifact-test-sync` | 测试用例 → 团队测试平台 | （纯编排） |
| `multica-artifact-ui-sync` | UI 规范 → 团队 UI 平台 | （纯编排） |

## 三、通用方法论 / 角色 / 评审（纯 Markdown，无脚本）

| Skill | 用途 |
|---|---|
| `multica-implementation` | 实现阶段方法论 |
| `multica-requirement-analysis` | 需求分析 |
| `multica-technical-design` | 技术设计 |
| `multica-verification` | 通用门禁 |
| `multica-test-design` | 测试设计 |
| `multica-test-automation` | 测试自动化 |
| `multica-gate-setup` | CI 硬门禁模板 |
| `multica-review-architect` | 架构评审 |
| `multica-review-backend` | 后端评审 |
| `multica-review-product` | 产品评审 |
| `multica-review-test` | 测试评审 |
| `multica-manage-skills` | 通过 Multica API 管理 Skill |

## 四、怎么挂载到 Multica

1. 把需要的 Skill 目录整体拷到你的 Multica workspace 的 `skills/` 下（目录名即 Skill 名，需与 `SKILL.md` 里的 `name` 字段一致）。
2. 含脚本的 Skill：先 `cp .env.example .env` 并填入你自己的 `JENKINS_URL` / `JIRA_URL` / `CONFLUENCE_URL` / `ATLASSIAN_USER` / `ATLASSIAN_PASS` 等，再按该 Skill 的 `README.md` 安装依赖、运行示例。
3. 平台层的 URL / 凭据**永远不要提交真实值**——保留 `.env.example` 占位即可。

## 五、命名约定

- 统一 `multica-` 前缀 + 小写连字符。
- 平台层只放占位外壳；真实基建信息由使用方在 `.env` 提供。
