# Skills 索引（zh_CN）

本目录收录可直接挂载到 [Multica](https://github.com/multica-ai/multica) 的共享 Skill。每个子目录即一个 Skill，`SKILL.md` 是给 Agent 读的技能说明；带脚本的 Skill 另附 `README.md` 给出人类视角的快速上手。

分层模型（详见 `docs/zh_CN/role-skills-architecture.md`）：**内容**（怎么写好）+ **编排**（落地到团队平台）+ **平台**（唯一连外部系统）+ **评审**（由非产出者执行）。

## 一、平台层（Platform，含占位外壳；真实 URL / 凭据由使用方在 `.env` 提供）

| Skill | 用途 | 主要入口 |
|---|---|---|
| `multica-platform-confluence` | 读写 Confluence 页面（URL / pageId → Markdown + 图片） | `scripts/confluence.sh`、`scripts/publish_design.py`、`scripts/fetch_page_by_url.py` |
| `multica-platform-jira` | 读写 JIRA issue、评论、状态流转、关联 issue | `scripts/jira.sh`、`scripts/get_issue.py` |
| `multica-platform-jenkins` | 触发 Jenkins 构建 / 发布 / 晋级 | `scripts/trigger_env.py`、`scripts/build_sit.py`、`scripts/promote_prod.py` |
| `multica-platform-apifox` | 同步 OpenAPI、补场景、跑批 | `lib/apifox.js`、`scripts/run_apifox.py` |
| `multica-platform-figma` | 读取 Figma 文件元数据 / 设计摘要 | `scripts/fetch_file.py` |

## 二、编排层（Orchestration，调用平台层把产物落地并回传稳定链接）

| Skill | 用途 | 主要入口 |
|---|---|---|
| `multica-artifact-req-sync` | PRD / 需求 → 团队需求平台（默认 Confluence + JIRA） | `scripts/publish-prd.sh` |
| `multica-artifact-design-sync` | 技术设计 → 文档平台 / Git | （纯编排） |
| `multica-artifact-api-sync` | API 契约 → 团队 API 平台（默认 Apifox） | （纯编排） |
| `multica-artifact-ui-sync` | UI 规范 → 团队设计平台（默认 Figma） | （纯编排） |
| `multica-artifact-frontend` | 前端实现说明 → 文档平台 | （纯编排） |
| `multica-artifact-cicd-sync` | 代码评审结论 → 触发 CI（默认 Jenkins），回传部署 URL | `scripts/trigger_cicd.py` |

## 三、内容层（Content，定义"写好"的标准）

| Skill | 用途 |
|---|---|
| `multica-requirement-analysis` | 需求分析：把需求结构化为编号 PRD |
| `multica-technical-design` | 技术设计草稿（含元数据与修订记录） |
| `multica-backend-impl` | 后端实现：契约先行 + TDD |
| `multica-frontend-impl` | 前端实现：体验与状态完整 |
| `multica-verification` | Leader 通用门禁：证据齐不齐、AC 对不对 |
| `multica-test-orchestration` | 测试跨阶段路由（T1/T2/T3）与裁决 |
| `multica-test-t1-design` | T1 功能用例：追溯矩阵 + 覆盖维度 |
| `multica-test-t2-coverage` | T2 覆盖率评估（对照 T1 与实现 diff） |
| `multica-test-t3-ui-automation` | T3 UI 自动化（1 CASE = 1 test） |
| `multica-test-t3-api-automation` | T3 接口自动化跑批 |

## 四、评审层（Review，由非产出者执行）

| Skill | 用途 |
|---|---|
| `multica-review-product` | 产品 / 价值评审 |
| `multica-review-architect` | 架构评审 |
| `multica-review-designer` | UI / 交互评审 |
| `multica-review-frontend` | 前端评审 |
| `multica-review-backend` | 后端评审 |
| `multica-review-test` | 测试评审 |

## 五、工具（Tooling）

| Skill | 用途 |
|---|---|
| `multica-gate-setup` | CI 硬门禁模板（分支保护 / delivery gate） |
| `multica-manage-skills` | 通过 Multica API 管理 Skill |

## 六、怎么挂载到 Multica

1. 把需要的 Skill 目录整体拷到你的 Multica workspace 的 `skills/` 下（目录名即 Skill 名，需与 `SKILL.md` 里的 `name` 字段一致）。
2. 含脚本的 Skill：先 `cp .env.example .env` 并填入你自己的 `JENKINS_URL` / `JIRA_URL` / `CONFLUENCE_URL` / `ATLASSIAN_USER` / `ATLASSIAN_PASS` 等，再按该 Skill 的 `README.md` 安装依赖、运行示例。
3. 平台层的 URL / 凭据**永远不要提交真实值**——保留 `.env.example` 占位即可。

## 七、命名约定

- 统一 `multica-` 前缀 + 小写连字符。
- 平台层只放占位外壳；真实基建信息由使用方在 `.env` 提供。
