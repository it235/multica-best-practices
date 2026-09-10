# Roadmap / 路线图

## v0.1（当前 / Current）

```text
Software Development Starter
├── 7 角色（Leader / Architect / Designer / FrontendDev / BackendDev / Tester / Reviewer）
├── 1 Squad（条件路由：任意角色可缺失）
├── 6 Skills
├── 1 Issue 模板（含「涉及端」范围声明）
└── 1 Workflow
```

## 内部版回流迁移 / Internal-edition back-migration

> 本仓库与一份内部版（CORP）同源分叉。以下为把内部版已验证能力回流到公开版的批次计划 / Batched plan for back-porting validated capabilities from the internal fork.

| 批次 | 内容 | i18n |
| --- | --- | --- |
| **B1** | 5 篇方法论文档（`FLOW` / `role-skills-architecture` / `test-automation-in-repo` / `multi-repo-and-issue-links` / `platform-collaboration`）+ `templates/MULTICA.md` | 双语同步 |
| **B2** | 新增 9 个 skill：`multica-backend-impl`、`multica-frontend-impl`、`multica-test-orchestration`、`multica-test-t1-design`、`multica-test-t2-coverage`、`multica-test-t3-ui-automation`、`multica-test-t3-api-automation`、`multica-platform-apifox`、`multica-platform-figma` | zh_CN 先行 |
| **B3** | 升级现有 skill（6 个 `multica-review-*`、`multica-technical-design`、`multica-pm-requirement-spec`、3 个 `multica-artifact-*-sync`、`multica-platform-jira` / `-confluence` 脚本增强、`multica-manage-skills`） | zh_CN 先行 |
| **B4** | agents / squad 同步；移除被取代的 `multica-test-design` / `multica-test-automation` / `multica-artifact-test-sync`；README / AGENTS / CHANGELOG 收尾 | 双语同步 |

### 迁移红线 / Migration red lines

- 不引入内部域名 / IP / 账号体系变量，一律占位化 / no internal hosts, IPs, or account-system env vars — placeholders only
- 不迁移绑定公司内部系统的实现（`multica-design-ui-impl` 的 BOSS / AngelAlign、`multica-platform-knowledge-base` 的 138 Bridge、`import_to_jira.py` 的 SynapseRT）/ skip company-coupled implementations
- 保留公开版既有 skill 名，只做内容升级、不做重命名 / keep public skill names; upgrade in place, no renames
- Skill 英文版可滞后，但 `docs/` 与根目录文档必须中英同步 / skill `en_US` may lag, but `docs/` and root docs stay in sync

## 近期 / Near term

- [x] Starter-first 结构：`templates/` 为唯一入口 / Starter-first structure with `templates/` as the only entry
- [x] Bug Fix Starter（跳过 Architect 的最小组合示范）/ minimal combo that skips Architect
- [x] 前后端拆分 + 条件路由（任意角色可缺失，Issue 声明「涉及端」）/ frontend/backend split with conditional routing
- [x] 国际化布局：README 双语切换 + `templates/`、`docs/` 按 `zh_CN/` / `en_US/` 双目录存放 / i18n layout with bilingual README and zh_CN/en_US template trees
- [ ] 产品流程编排验证：完整流程 / 无设计 / 无前端 / 无后端 四种小队跑真实需求 / validate four squad variants on real requirements
- [ ] Technical Research Starter（Researcher → Leader 判门（multica-verification skill）→ Human）
- [ ] 更多技术栈验证命令对照表（Java、Rust、monorepo）/ more stack-specific verification command tables
- [ ] 填好假数据的真实试点复盘示例 / real pilot retro example with sample data

## 更远 / Later

- [ ] 更多真实案例与社区反馈 / more real cases and community feedback
- [ ] 模型适配指南（弱模型 vs 强推理模型的分工建议）/ model-fit guide (weak vs strong models)
- [ ] 可选 Multica Skill 包发布到 Skill Registry / optional Skill pack on the Skill Registry

## 什么时候才算 Stable / When is it Stable

不是模板写完了，而是**不同项目、不同 Agent、不同模型跑过足够多真实 Issue**。
Not "templates are written," but enough real Issues run across different projects, agents, and models.

## 与相关项目的关系 / Relationship to related projects

- 与 **oh-my-multica**（确定性交付 Loop / DAG）互补 / complements oh-my-multica (deterministic delivery Loop / DAG)
- 与 **multica-agent-workflow-template**（Agent 数量与 Skill 路由设计）互补 / complements multica-agent-workflow-template (agent count & skill routing design)
- 本仓库聚焦：Squad Instructions、门禁约定、Starter 模板、团队推广 / this repo focuses on Squad Instructions, gate conventions, Starter templates, and team rollout

## 非目标 / Non-goals

- 不在本仓库内构建编排引擎 / no orchestration engine inside this repo
- 不绑定单一 CLI 或模型供应商 / no single CLI or model-vendor lock-in
