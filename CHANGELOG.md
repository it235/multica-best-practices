# Changelog / 更新日志

All notable changes to this project will be documented in this file.
本文件记录本项目的所有重要变更。新条目采用中英结合写法（Chinese-first, English alongside）。

## v0.0.14 - 2026-09-10 · 修复 apifox skill 内容污染 + 补齐 review-test frontmatter / Fix corrupted apifox skill & missing frontmatter

### Fixed / 修复

- **问题 A（严重）`multica-platform-apifox` 内容被全局 `a→p` 替换污染**：v0.0.12 的脱敏批量替换规则出错，该目录 25/28 个文件损坏 —— `name:` → `npme:`、`apifox` → `ppifox`、`install` → `instpll`、`api_base_url` → `ppi_bpse_url`、`sync_openapi.js` → `sync_openppi.js` 等，frontmatter、脚本引用、命令示例、config 字段名均不可用，与 README「复制粘贴就能用」的承诺冲突。
  已**从干净源头整体重导该目录**（28 个文件，文件清单与污染版一致），并对内网域名做**定向**替换（`apifox.<内部域名>` → `apifox.example.com`，10 个文件）；**未再做任何全局字符替换**。/ the whole directory was re-exported from a clean source; only the internal host was replaced, no global character substitution.
- **问题 B（轻微）`multica-review-test/SKILL.md` 缺失 frontmatter**：zh_CN 30 个 skill 中唯一缺少 `name:` / `description:` 的一个，导入工具读不到 name（靠目录名兜底）与 description（直接丢失）。已参照 en_US 版补齐，description 按中文正文改写。

### Security / 安全

- 复核：全仓 `templates/` 已无公司内网域名残留；30 个 SKILL.md 均有完整 frontmatter；apifox 目录污染特征归零，JS（12 个）与 Python 语法校验通过
- 后续改进：脱敏必须**定向替换具体值**，禁止对整目录做无约束的字符级全局替换

## v0.0.13 - 2026-09-09 · 新增自动化同步脚本：一键建队 / Automation scripts: one-shot squad bootstrap

### Added / 新增

- **`scripts/multica-sync/`**：可选的模板推送自动化（Python 3.9+，仅标准库），把 `templates/zh_CN` 推送到 Multica workspace
- **`bootstrap_squad.py`**：一键建队主脚本，5 步幂等流水线 —— 导入 skills → 创建/更新 agents → 创建小队 → 加成员 → 绑定 skills；支持 `--dry-run` / `--sync-skills` / `--bind-mode` / `--only` / `--runtime` / `--write-mapping`
- **`repo_paths.py`**：模板路径解析（`templates/zh_CN` 优先，兼容平铺布局；`MULTICA_TEMPLATES_DIR` / `MULTICA_TEMPLATE_LANG` 可覆盖）
- **`squad-bootstrap.example.json`**：15 个角色的完整引导配置（角色 → skills 挂载），使用本仓库当前 skill 命名
- **配置缺省即用**：`bootstrap_squad.py` 不传 `--config` 时自动回退到内置的 `squad-bootstrap.example.json`，最快两条命令即可建队

### Changed / 变更

- **`multica_client.py` 扩展**：新增 `create_squad` / `update_squad` / `add_squad_member` / `list_squads` / `create_agent` / `add_agent_skills` / `set_agent_skills` / `list_runtimes`
- **AGENTS.md / README（中英）** 仓库结构补充 `scripts/` 说明，并在核心约定中加入「自动化配置驱动且不含机密」
- **5 分钟快速开始拆为两种模式**：**方式 A 自动**（脚本，一条命令建好整套）/ **方式 B 手工**（复制粘贴 Step 1–3）；Step 4–6（建 Issue → 分配 → 运行）两种模式共用
- **主流程表述修正（中英）**：`需求收敛(G0) → 设计 → 实现 → 单测 → 部署 → 自动化测试` —— 原「测试」明确为**单测**（实现阶段内完成），**自动化测试**（T3）明确置于**部署之后**（对应 G2.5 部署 → T3 跑自动化）
- **标语微调（中英 + AGENTS）**：`Copy. Paste. Run.` 后补「复制即用；或者一条命令自动建好整套」，覆盖脚本自动模式

### Security / 安全

- **脱敏**：脚本内不内置任何 host / token / workspace / ID；地址解析顺序为 `--url` > `MULTICA_API_URL` > `config.local.json`（git-ignored）
- 以**名称**为对齐键（agent / skill / squad 名），无需提交任何 UUID；`agent-mapping.example.json` 示例值已全部改为占位

## v0.0.12 - 2026-09-05 · 内部版回流迁移批次 2–4：Skills 全量回流 + 脱敏闭环 / Internal back-migration batches 2–4: full skill back-migration + desensitization closed-loop

### Added / 新增（回流自内部版，已脱敏）

- **新增 10 个 skill（zh_CN）**：`multica-backend-impl`、`multica-frontend-impl`、`multica-artifact-frontend`、`multica-test-orchestration`、`multica-test-t1-design`、`multica-test-t2-coverage`、`multica-test-t3-ui-automation`、`multica-test-t3-api-automation`、`multica-platform-apifox`、`multica-platform-figma`
- **升级 15 个现有 skill（zh_CN，就地覆盖为内部版更成熟内容）**：`multica-review-*`（×6）、`multica-technical-design`、`multica-verification`、`multica-artifact-cicd-sync`、`multica-platform-jira`、`multica-platform-confluence`，以及内部版已重命名的 4 个：`multica-pm-requirement-spec`→`multica-requirement-analysis`、`multica-pm-artifact-publish`→`multica-artifact-req-sync`、`multica-artifact-architect`→`multica-artifact-design-sync`、`multica-artifact-backend`→`multica-artifact-api-sync`
- **`MULTICA.md` 机制落地**：产品仓库根目录上下文模板（layout / 测试自动化路径 / 构建验证命令 / 分支约定），分仓各一份，缺失即 BLOCKED

### Changed / 变更

- **移除被取代的 3 个 skill（zh + en）**：`multica-test-design`、`multica-test-automation`、`multica-artifact-test-sync`，统一由 `multica-test-orchestration` + `multica-test-t1/t2/t3-*` 取代
- **全局引用更新**：agents / squad（zh+en）/ docs（zh+en）/ README（zh+en）/ skills 索引 全部改指向新 skill 名；`multica-design-ui-impl`、`multica-platform-knowledge-base` 等未随附能力标记为「可选、本仓库未随附」
- **脱敏闭环**：内部域名 / IP / 域账号变量 / 业务系统名 / 项目 Key / 138 Bridge 全部替换为占位或通用示例；凭据与平台基址一律走环境变量 / `.env`（如 `JIRA_USERNAME`、`ATLASSIAN_PASS`、`APIFOX_API_BASE_URL`、`TEAM_KB_URL`）
- **`templates/zh_CN/skills/README.md`** 重写为四层（内容 / 编排 / 平台 / 评审）索引
- **ROADMAP 红线更新**：明确 `multica-implementation` 保留（未被取代）

### Migration notes / 迁移说明

- **未迁移**（绑定公司内部系统，已在 ROADMAP 红线记录）：`multica-design-ui-impl`（BOSS 母版 / AngelAlign）、`multica-platform-knowledge-base`（138 Bridge）、`import_to_jira.py`（SynapseRT，改为团队自备脚本 + `references/import-contract.md` 约定）
- **Skill 英文版滞后**：本次 zh_CN 全量回流；`en_US/skills` 仍为旧版（仅移除被取代项、修正失效引用），新增 / 升级内容待 B2–B3 完成后补齐，状态在 CHANGELOG 跟踪 / skill `en_US` lags behind `zh_CN` and is tracked here
- 后续：完善 `en_US/skills` 双语、补齐 `software-development-reviewed` squad 与 agents 的细化挂载 / finish `en_US/skills` i18n and the reviewed-Starter wiring

## v0.0.11 - 2026-09-05 · 内部版回流迁移批次 1：方法论文档 + MULTICA.md / Internal back-migration batch 1: methodology docs + MULTICA.md

### Added / 新增

- `docs/zh_CN/FLOW.md` + `docs/en_US/FLOW.md` — 交付物驱动的完整流程：纠正「产出角色必须依次出场」的误解，改为「工作包 Required 才入场」；单交付物两层闭环（Reviewer 驳回后**必须重跑验证**再复审）、动态主流程、验证/评审子循环、时序图、工作包表、三种典型裁剪、Leader 检查清单 / Deliverable-driven flow: work packages enter only when Required; after a Reviewer rejects, verification must be re-run before re-review
- `docs/zh_CN/role-skills-architecture.md` + `docs/en_US/role-skills-architecture.md` — Skill **四层模型**（内容 / 编排 / 平台 / 评审）与分层判定法「换个公司会不会改写」；含角色 → skill 挂载矩阵与常见错误 / four-layer skill model and the "would this change if we changed company" test
- `docs/zh_CN/test-automation-in-repo.md` + `docs/en_US/test-automation-in-repo.md` — 自动化资产入仓约定：正文在团队平台、可执行脚本入 Git，**路径只读产品仓根目录 `MULTICA.md`**，缺文件即 BLOCKED / automation assets: prose on the team platform, scripts in Git, paths owned by `MULTICA.md`
- `docs/zh_CN/multi-repo-and-issue-links.md` + `docs/en_US/multi-repo-and-issue-links.md` — 多仓矩阵是唯一事实源（Multica 不会自动识别）；关联 Issue 上游必读清单与角色读法 / the repo matrix is the single source of truth; mandatory upstream reads for linked Issues
- `docs/zh_CN/platform-collaboration.md` + `docs/en_US/platform-collaboration.md` — 平台能力只写一份：URL / 凭据 / REST 细节只存在于 `multica-platform-*`，角色 skill 只声明「读什么、写什么、调谁」/ platform capability written exactly once
- `templates/zh_CN/MULTICA.md` + `templates/en_US/MULTICA.md` — 产品仓库根目录上下文模板：layout、测试自动化路径（分仓各一份）、构建与验证命令、分支约定、凭据**只写变量名** / repo-root context template: layout, automation paths, build commands, branches, credential variable names only

### Changed / 变更

- `docs/zh_CN/where-to-put-things.md` + `docs/en_US/where-to-put-things.md`：速查表新增 5 行（能力该放哪层 / 平台细节放哪 / 流程怎么裁剪 / 多仓怎么路由 / 自动化脚本放哪）/ cheat sheet gains 5 rows
- `README.md` + `README.en.md`：文档表新增 `FLOW`、`role-skills-architecture`、`platform-collaboration`、`test-automation-in-repo`、`multi-repo-and-issue-links` 五个条目 / docs table gains five entries
- `ROADMAP.md`：新增「内部版回流迁移 / Internal-edition back-migration」四批次计划与四条迁移红线 / adds the four-batch back-migration plan and four red lines
- `AGENTS.md`：结构图补 `MULTICA.md` 与新增方法论文档；三层模型扩展为**四层**（内容 / 编排 / 平台 / 评审）并说明 `MULTICA.md` 机制 / structure diagram and the three-layer model extended to four layers

### Migration notes / 迁移说明

- 回流自内部分叉版本，**已脱敏**：移除内部域名 / IP / 域账号变量（`SHIDAITS_DOMAIN_*` → `ATLASSIAN_USER` / `ATLASSIAN_PASS`）、内部系统名（BOSS / AngelAlign / SynapseRT / 138 Bridge）、公司项目名示例（`cds-*` → `acme-*`）/ desensitized: internal hosts, account env vars, internal system names and project examples replaced with placeholders
- **未迁移**（绑定公司内部系统，记录在 ROADMAP 红线）：`multica-design-ui-impl`（BOSS 母版 / AngelAlign 规范）、`multica-platform-knowledge-base`（138 Bridge）、`import_to_jira.py`（SynapseRT）/ skipped as company-coupled
- **Skill 英文版滞后**：本批次只落地 `docs/` 与根目录文档的双语；新增 / 升级的 skill 先保证 `zh_CN`，`en_US` 在 B2–B3 完成后补齐并在此文件追踪 / skill `en_US` lags behind `zh_CN` and is tracked here as pending
- 后续批次：B2 新增 9 个 skill、B3 升级现有 skill、B4 agents / squad 同步与收尾 / upcoming: B2 adds 9 skills, B3 upgrades existing ones, B4 syncs agents/squads

## v0.0.10 - 2026-08-22 · 全量 Review 修复：一致性/双语文档同步 / Full-review fixes: consistency & bilingual sync

### Changed / 变更

- `bug-fix/squad.md`（中英）：【团队】段移除 `@Architect` / `@Designer`，与「Bug 修复不经过 Architect」的核心设计一致；影响端只有前端 / 后端，不再误列设计端 / Bug squad removes Architect & Designer from the team list to match the "no Architect" design
- `bug-fix/squad.md`（中英）+ `software-development/squad.md`（中英）：第一步/需求就绪补充「链接型 Issue 按 `<ISSUE-KEY>` 或链接去外部系统取回需求/范围/验收标准」的取数指引，与 issue.md 的「来源二选一」对齐 / Squad instructions now pull requirements for linked Issues from the external system
- `README.md` / `README.en.md`：Issue 模板描述由「含 Git 分支」改为「来源支持链接型 / 全量自包含二选一」（issue.md 已在 v0.0.9 删除 Git 分支章）/ Root READMEs drop the stale "Git branch" claim
- `en_US/squad/software-development/README.md`：目录表「Shared Skills」数量由遗留的 6 修正为 16，与正文一致 / en starter README fixes the stale "6 Skills" count
- `software-development/issue.md`（中英）+ `bug-fix/issue.md`（中英）：「为什么这么写」字段列举与模板实际章节（参考资料 / 备注、References / Notes）对齐；bug-fix 补「常见失败」段，与 software-development 体例一致 / Issue "why" sections list the real sections; bug-fix adds a "common failure modes" section
- `agents/devops.md`（中英）+ `skills/multica-platform-jenkins/SKILL.md`（中英）：移除对已删除的 Issue「Git 分支」区块的引用，deploy branch 改为「由 Issue 来源与涉及端确定，链接型以外部系统分支为准」/ DevOps & Jenkins skill drop the stale reference to the removed Issue "Git Branch" block
- `agents/backend-developer.md`（中英）：「为什么有效」补「契约由后端 owner、架构师只给方案与步骤」的分工说明；并将「自证」改为「自查证据」，明确用 `multica-verification` 跑的是自查、判门权只在 Leader / Backend Dev doc clarifies the contract-owner split and that self-check ≠ Leader gate

### Why / 背景

- 全量 Review 发现上述文档在多次演进后留下数字遗漏、与已删除章节不符的声称、以及 Squad 指令未接入轻量链接型用法等问题；本次集中修正，保证「复制即运行」不踩坑 / Full-review sweep fixed leftover counts, stale claims, and Squad instructions lagging behind the lightweight Issue mode

## v0.0.9 - 2026-08-22 · Issue 模板支持双形态（Jira/Tapd 链接型轻量填写）/ Issue template dual-form: lightweight Jira/Tapd link mode

### Changed / 变更

- `software-development/issue.md`（中英）新增「Issue 来源（必填，二选一）」块：支持「外部系统链接（轻量）」只填链接 + 涉及端 + 一句话摘要，或「全量自包含」完整填写；底部「为什么这么写」补充来源分流说明 / Issue template adds "Issue source (pick one)" — lightweight external-link mode vs fully self-contained
- `bug-fix/issue.md`（中英）同步新增「Issue 来源（必填，二选一）」块 / Bug issue template gets the same "Issue source (pick one)" block
- `software-development/README.md`（中英）文件清单与 Step 4、根 `README.md` / `README.en.md` Step 4 描述更新，反映链接型轻量用法 / Starter READMEs + root READMEs updated to mention link-style filling
- `software-development/issue.md`（中英）修正角色错配：需求追踪矩阵改标「提 Issue 留空、由 Tester 回填」；技术上下文改选填（Architect 在 G1 补全）；约束拆「业务约束（PM 填）/ 工程约束（Architect 补）」；验证方式降为「期望验证维度（示意，Leader/Tester 定）」；根 README 流程补「需求收敛(G0)」阶段 / Issue template fixes role mismatch: matrix is Tester-backfilled, context is optional, constraints split, verification is indicative; root README flow adds G0
- `software-development/issue.md`（中英）进一步精简：删除「需求追踪矩阵 / 技术上下文 / 约束 / 验证方式 / Git 分支」五章，仅保留背景/目标/范围(含涉及端)/非目标/验收标准/来源/参考资料/备注，模板回到纯需求契约 / Issue template trimmed: drop matrix/context/constraints/verification/Git-branch; keep requirement-contract sections only

### Why / 背景

- Issue 真实形态有两种：Jira/Tapd 链接（全量需求在外部系统）与全量自包含 Markdown。原模板默认全量、对链接型过重；新增来源分流后，链接型只需「链接 + 涉及端 + 摘要」即可驱动 G0 路由与 multica-verification 门禁，两种形态共用同一 `<ISSUE-KEY>` / Issues come in two real forms; the source selector lightens link-type Issues while keeping gates intact
- 提 Issue 者通常是 PM（一个 Issue 即一个需求），而追踪矩阵/技术上下文/工程约束/验证方式属下游角色产物。前置成 PM 必填会凭空编 ID 或写入过期信息；Issue 应只作需求契约（为什么做 / 做什么 / 验收 / 非目标），其余由 Squad 运行中回填 / The filer is usually a PM; matrix/context/constraints/verification are downstream artifacts, not requirement inputs

## v0.0.8 - 2026-08-20 · CI/CD gate + Tester three-phase + DevOps role + platform shells / CI/CD 门禁、Tester 三阶段、DevOps 角色与平台层占位壳

### Added / 新增

- 新增 `DevOps` 角色（`templates/zh_CN/agents/devops.md`）：G2 PASS 且代码已 push 后触发 CI/CD、回传部署环境 URL，不写业务代码 / New `DevOps` agent: triggers CI/CD after G2, returns deploy URL, no business code
- 新增 5 个平台层占位壳 skill（不带内网地址/凭据，仅占位）：`multica-platform-confluence`、`multica-platform-jira`、`multica-platform-jenkins`、`multica-artifact-cicd-sync`、`multica-test-automation` / Added 5 platform-layer shell skills (no internal URLs/credentials, placeholder only)
- 新增 `docs/zh_CN/cicd-and-test-pipeline.md`：G2.5 与 Tester T1/T2/T3 方法论、deploy branch 模型 / New `docs/zh_CN/cicd-and-test-pipeline.md` methodology
- `artifact-conventions.md`（中英）新增「三层架构：内容/编排/平台」与 PM/Architect 双 skill 标准用法 / `artifact-conventions.md` (zh/en) adds three-layer architecture + dual-skill usage
- 角色计数 8 → 9（新增 DevOps）；Skill 11 → 16（新增 5 平台层壳）/ Roles 8 → 9 (DevOps); Skills 11 → 16 (5 platform shells)

### Changed / 变更

- `gates-and-evidence.md`（中英）门禁表新增 **G2.5（CI/CD 部署）** 行 + 走查示例 / `gates-and-evidence.md` (zh/en) adds **G2.5** row + walkthrough
- `tester.md`（中英）升级为 **T1/T2/T3 三阶段**（T1 用例、T2 覆盖率、T3 部署后自动化），移除具体平台绑定 / `tester.md` (zh/en) upgraded to T1/T2/T3 three-phase
- `leader.md`（中英）路由新增 PM 首派、Tester 三阶段路由、DevOps/G2.5 路由 / `leader.md` (zh/en) routing adds PM-first, Tester three-phase, DevOps/G2.5
- `product-manager.md`（中英）增加「先 `multica-requirement-analysis` 结构化，再 `multica-artifact-req-sync` 落地」双 skill 句式 / `product-manager.md` (zh/en) gains dual-skill pattern
- `software-development/squad.md` 与 `issue.md`（中英）阶段表加入 G2.5 与 deploy branch 声明；issue 模板新增「Git 分支」区块 / Squad & issue add G2.5 + deploy branch
- AGENTS.md 结构图更新为 9 角色 + 平台层占位壳 + 三层模型说明 / AGENTS.md structure updated to 9 roles + platform shells + three-layer model

### Removed / 移除

- 无真实内网地址/凭据进入公开仓库：所有 platform skill 仅占位壳，接入时由团队填 `config.yaml` / No real internal URLs/credentials enter the public repo; platform skills are placeholder shells only

## v0.0.7 - 2026-08-17 · Artifact platform decoupled into skills / 产物平台对接下沉到 skill

### Added / 新增

- 新增 5 个产物对接 skill（中英，每个默认平台可替换）：`multica-artifact-req-sync`（PRD→Confluence）、`multica-artifact-ui-sync`（UI→Figma）、`multica-artifact-design-sync`（技术设计→Git/Confluence）、`multica-artifact-api-sync`（API 契约→Apifox）、`multica-artifact-test-sync`（用例→本地 XMind 转 Jira）/ Added 5 artifact-sync skills (zh/en, swappable default platform each)
- 新增 `artifact-conventions.md`（中英）重写为「产物内容规范 + 对接 skill」：内容归角色、平台归 skill，角色提示词不写平台名；换公司只换 skill / Rewrote `artifact-conventions.md` (zh/en) into "content spec + sync skill": content belongs to role, platform to skill; no platform name in prompts
- `README.md` / `README.en.md` Skill 表加 5 个 `multica-artifact-*-sync` 条目，计数 6→11 / README skill tables add the 5 artifact-sync skills, count 6→11

### Changed / 变更

- 全部 8 个角色指令（中英）：「我产出什么 / WHAT I PRODUCE/OWN/DELIVER」改为"用 `multica-artifact-*-sync` skill 落地并回传稳定链接"，去掉写死的 `artifacts/<issue-id>/xxx.md` 与本地产平台名（如 Designer 的 Figma）/ All 8 agent instructions (zh/en): outputs now "land via multica-artifact-*-sync and return a stable link", dropping hard-coded local paths and platform names
- `templates/zh_CN|en_US/squad/software-development/squad.md`：阶段表与产物流水线改为"角色经 skill 回传链接"，【产物落盘】段改为【产物落盘与取回】，不再写死本地路径 / Squad stage map & pipeline now say "role returns link via skill"; 【ARTIFACT LANDING】 becomes landing+retrieval, no hard-coded local paths

## v0.0.6 - 2026-08-17 · Artifact landing conventions / 协作产物落盘约定

### Added / 新增

- 新增 `artifact-conventions.md`（中英）：规定所有阶段产物统一落 `artifacts/<issue-id>/`，文件名固定（PRD=`prd.md`、技术设计=`design-tech.md`、UI 设计=`design-ui.md`、API 契约=`api-contract.md`、功能用例=`cases-feature.md`、接口用例=`cases-api.md`、测试报告=`test-report.md`、验收=`acceptance.md`）；下游用相对路径定位，绝不写绝对路径 / 不泄露 workspace / 不靠搜索 / 引用必须显式传路径 / 冲突以哪份为准 / 产物变更路径不变内容更新 / 门禁据此重判 / 文档表与常见错误同步 / Added `artifact-conventions.md` (zh/en): all stage artifacts land under `artifacts/<issue-id>/` with fixed filenames; downstream locates by relative path
- `where-to-put-things.md`（中英）加一行：协作产物放哪 → `artifacts/<issue-id>/`（见 artifact-conventions）/ where-to-put-things gains an artifact-landing row
- `README.md` / `README.en.md` 文档表加 `artifact-conventions` 条目 / README doc tables add the artifact-conventions entry

### Changed / 变更

- `templates/zh_CN|en_US/squad/software-development/squad.md`：阶段表与产物流水线每个产物标注落盘路径；新增【产物落盘】段，要求 Leader 派活时显式给出产物路径 / Squad stage map & artifact pipeline now annotate each artifact's landing path; added 【ARTIFACT LANDING】 rule requiring explicit path in dispatch
- 全部 8 个角色指令（中英）的「我产出什么 / WHAT I PRODUCE/OWN/DELIVER」补落盘路径与"读取上游 `artifacts/<issue-id>/...`"的硬指示，下游据此定位上游产物 / Every agent instruction (zh/en) now states its artifact landing path and reads upstream via `artifacts/<issue-id>/...`

## v0.0.5 - 2026-08-17 · Add ProductManager role + AI-readable requirement discipline / 新增产品经理角色与需求 AI 可读纪律

### Added / 新增

- 新增 `ProductManager` 角色指令（`templates/zh_CN|en_US/agents/product-manager.md`）：把想法 / 诉求 / 会议结论整理成可评审、可设计、可开发、可测试的 PRD（含 G-/FR-/BR-/AC-/KPI-/RISK-/OP- 编号、六类读者对准、需求类型→产物形态、AI 可读纪律、协作偏好）/ New `ProductManager` agent instructions: turns ideas / asks / meeting notes into reviewable PRDs
- 角色词表加入 `ProductManager`，`naming-conventions.md`（中英）第 2 条同步 / Role vocabulary now includes `ProductManager` in `naming-conventions.md` (zh/en)
- 软件开发展望 Starter 接入 PM：团队段加 @ProductManager，阶段表加 S0 需求产出 @ProductManager → G0 范围确定（基于 PRD），产物流水线加第 0 步；无 PM 时 Issue 直接视为就绪范围、跳过 S0 / software-development Squad wires in PM: S0 requirement @ProductManager → G0 scope; without PM, Issue is the ready scope
- `gates-and-evidence.md`（中英）新增「需求 / 设计类产物的 AI 可读纪律」：稳定标题、稳定表格字段、规则编号、待确认集中（OP- 未关闭不进开发）、文档互链、冲突指明准绳、禁用模糊词、规则文字化；违反任一条 G0/G1 判 REJECTED / Added "AI-readable discipline for requirement / design artifacts" to `gates-and-evidence.md` (zh/en)
- Starter 角色计数 7 → 8（`templates/zh_CN|en_US/squad/software-development/README.md`）/ Starter role count 7 → 8

### Changed / 变更

- @Designer / @Architect（中英）的「产品需求」来源改为以 @ProductManager 的 PRD 为主（无 PM 退化到 Issue / @Architect 说明），并明确产品范围 / 业务规则 / 字段口径归 PM、无 PM 归 Leader 收敛 / Designer & Architect now take PRD from @ProductManager as the primary source; product scope / business rules / field definitions belong to PM (or Leader without PM)

## v0.0.4 - 2026-08-17 · Three-segment naming (role + project + member-id) / 命名升级为三段式

### Changed / 变更

- 命名规范从「角色 + 实例」升级为「角色 + 项目 + 成员标识」`<角色>-<项目>-<成员标识>`，解决「真实姓名 vs 角色名」冲突：同项目同角色多人时靠成员标识（工号/花名，不用真实姓名全称）唯一区分 / Upgraded naming from `role + instance` to `role + project + member-id` `<role>-<project>-<member-id>` to resolve the "real name vs role name" collision: same project + same role + multiple people are disambiguated by the member-id (employee number / nickname, never a full real name)
- 角色前缀通配解析同步扩为三段：`@角色` → 指挥按 `@角色-<本小队 suffix>-<本小队 member>` 精确 @mention（suffix 对应 `<项目>` 段，member 对应 `<成员标识>` 段）/ Role-prefix wildcard resolution extended to three segments: `@role` → orchestrator dispatches `@role-<squad suffix>-<squad member>`
- 同步更新 `docs/zh_CN|en_US/naming-conventions.md`、`templates/zh_CN|en_US/squad/{software-development,bug-fix}/squad.md` 与 `templates/zh_CN|en_US/agents/leader.md` 的前缀解析段/精确派活描述，以及 README（中英文）、AGENTS.md、adapt-and-scale.md（中英文）、各 squad README 的命名标题引用 / Synced all references in README (zh/en), AGENTS.md, adapt-and-scale.md (zh/en), and each squad README

### Removed / 移除

- 未采纳「私有小队 Profile」机制（用户判定过于复杂，不引入）/ Did not adopt the "private squad Profile" mechanism (deemed too complex by the user)

## v0.0.3 - 2026-08-17 · Squad instructions re-leveled to Squad scope / Squad 指令重构为 Squad 级

### Changed / 变更

- Squad 指令（`templates/zh_CN/squad/software-development/squad.md` 与 `templates/en_US/...`，以及 `templates/zh_CN/squad/bug-fix/squad.md` 与 `templates/en_US/...`）改为真正的「Squad 级」：开场定义 Squad 目标 / 事实来源与待确认项 / 编号规范（G-/U-/FR-/BR-/AC-/KPI-/OP-/RISK-，software-development）/ 沟通风格 / 禁止事项（software-development），对所有角色成立；原「你是 Leader」内容下移为独立的 `【Leader 角色】` 段，明确 Leader 仅编排、推进权与判门权在 Leader。借鉴了通用写法但去掉了任何具体项目、工具链与智能体人名的绑定，保持可复制 / Re-leveled the Squad instructions to true squad scope (both `software-development` and `bug-fix`, in zh_CN and en_US): the opening now defines the Squad goal, fact-source & TBD policy, numbering convention (software-development), communication style, and prohibited list (software-development), valid for every role; the former "you are the Leader" content moved into a standalone `【Leader Role】` section stating the Leader only orchestrates and holds advancing/gating authority. Borrowed generic patterns but dropped any binding to specific projects, toolchains, or agent names to stay copy-paste-ready

### Added（追加 · 门禁纪律增强 / Gate discipline enhancements）

- 在 Squad 级规则中补充三条判门纪律（中英文 squad.md 均落地）：(1) 范围内某产物判定为「不适用（N/A）」必须显式标注 + 理由 + Leader 确认，禁止静默跳过；(2) 任一产物被修改后下游门禁立即失效必须重判，不得沿用旧 PASS（不仅实现变更，设计 / API 契约 / 用例变更同样失效）；(3) 同一产物判门连续 3 次 FAIL 强制升级人类，而非无限返工 / Added three gate disciplines to the Squad-level rules (both zh_CN and en_US squad.md): (1) an in-scope artifact judged N/A must be marked explicitly with reason + Leader confirmation — never silently skipped; (2) once any artifact is modified its downstream gates are invalidated and must be re-judged, never carry over an old PASS (not just implementation — design / API contract / case changes also invalidate downstream); (3) the same artifact failing the gate 3 times in a row escalates to Human instead of endless rework
- 同步 `docs/zh_CN` 与 `docs/en_US` 的 `gates-and-evidence.md`（扩展门禁失效原则，覆盖上游产物修改与 N/A 不静默跳过）和 `common-mistakes.md`（新增第 9 条「静默把范围内产物当 N/A 跳过」错误示范，并扩展诊断清单）/ Synced `gates-and-evidence.md` (extended gate-invalidation principle to upstream changes and non-silent N/A) and `common-mistakes.md` (new pitfall #9 on silently skipping in-scope artifacts as N/A, plus expanded diagnostic checklist) in both `docs/zh_CN` and `docs/en_US`

### Added（追加 · 借鉴邻方案的四项增强 / Borrowed enhancements）

- **角色前缀通配解析**（解决「workspace 内多个同角色实例如何锁定本小队」）：新增 `docs/zh_CN|en_US/naming-conventions.md` 的「小队实例后缀与前缀通配」规则——Squad 指令只写角色前缀（@FrontendDev 等），小队启动时声明实例后缀 suffix，指挥按 `@角色-<本小队 suffix>` 精确 @mention；并在两个 `squad.md`（中英文）+ `agents/leader.md`（中英文）补「角色前缀解析」段与精确派活规则 / **Role-prefix wildcard resolution** (solves "how to pin this squad's agent among multiple same-role instances in a workspace"): added "Squad instance suffix & prefix wildcard" to `docs/zh_CN|en_US/naming-conventions.md` — Squad instructions write only the role prefix, the squad declares a suffix at startup, and the orchestrator dispatches `@role-<squad suffix>`; also added a "role prefix resolution" section and precise-dispatch rule to both `squad.md` (zh_CN/en_US) and `agents/leader.md` (zh_CN/en_US)
- **门禁结论四值与汇合门禁 + 判门不改产物**（落到 `docs/zh_CN|en_US/gates-and-evidence.md`）：新增 APPROVED / APPROVED_NA / REJECTED / BLOCKED 四值（APPROVED_NA 区别于普通 PASS 的下游差异由 Leader 写明）；明确汇合门禁「并行分支须全 PASS 才开放下游」；判门者只给结论与修改清单、不代替作者改产物 / **Four verdict values, join gates, gatekeeper-doesn't-edit** added to `docs/zh_CN|en_US/gates-and-evidence.md`: APPROVED / APPROVED_NA / REJECTED / BLOCKED (APPROVED_NA's different downstream is stated by the Leader); join gates require every parallel branch PASS; the gatekeeper only gives a verdict + fix list and never edits the artifact
- **阶段-门禁对照表**（落到 `templates/zh_CN|en_US/squad/software-development/squad.md` 顶部）：以 `@角色` 占位、不写死人数/人名的 S0–G4 流水线一览，缺层即跳过对应行 / **Stage-gate map** added atop `templates/zh_CN|en_US/squad/software-development/squad.md`: a S0–G4 pipeline overview using `@role` placeholders (no hardcoded counts/names), skipping the line for any missing layer
- **需求追踪矩阵**（落到 `templates/zh_CN|en_US/squad/software-development/issue.md`）：建议 REQ → DESIGN → API → CODE → CASE → TEST 映射，保证验收标准无断链 / **Requirements traceability matrix** added to `templates/zh_CN|en_US/squad/software-development/issue.md`: suggested REQ → DESIGN → API → CODE → CASE → TEST mapping to prevent broken links
- **判门不改产物**同步进 squad.md 推进规则与 bug-fix 规则（中英文）及 leader.md 第 9 条 / **Gatekeeper-doesn't-edit** also synced into the advance rules of both squad.md (zh_CN/en_US, software-development + bug-fix) and leader.md rule #9 (zh_CN/en_US)

### Added（追加 · 新增 Designer 角色 / New Designer role）

- 新增 `Designer` 角色，专做 UI / 交互设计、对接 Figma 出视觉与标注，与 `Architect`（技术架构设计）明确分离；新建 `templates/zh_CN|en_US/agents/designer.md` / Added a **Designer** role for UI / interaction design working with Figma, separated from `Architect` (technical design); new `templates/zh_CN|en_US/agents/designer.md`
- `docs/zh_CN|en_US/naming-conventions.md` 角色词表加入 `Designer`，并注明 Architect ≠ Designer / `docs/zh_CN|en_US/naming-conventions.md` role vocabulary now includes `Designer`, noting Architect ≠ Designer
- 两个 `squad.md`（中英文）的【团队】段加入 `@Designer`；software-development 的阶段-门禁对照表拆分为 S1a 技术设计(@Architect) / S1b UI 设计(@Designer) 双线，并明确 @FrontendDev 同时依赖二者；bug-fix 团队段也加入 @Designer（UI bug 场景）/ Both `squad.md` (zh_CN/en_US) gained `@Designer` in the team section; software-development's stage-gate map splits into S1a technical design (@Architect) / S1b UI design (@Designer) with @FrontendDev depending on both; bug-fix team section also lists @Designer
- `frontend-developer.md`（中英文）明确 UI 来源为 @Designer 的 Figma 产出，缺位时回退设计文档或 mock / `frontend-developer.md` (zh_CN/en_US) now names @Designer's Figma output as the UI source, falling back to a design doc or mock when absent
- 同步角色计数：README / README.en / ROADMAP / AGENTS.md / software-development README 由 6 角色更新为 7 或 5→6 Agent / Synced role counts in README / README.en / ROADMAP / AGENTS.md / software-development README (6→7 roles, or 5→6 agents)

## v0.0.2 - 2026-08-16 · Template correctness fixes / 模板正确性修复

### Changed / 变更

- 修复 CI 门禁模板：结构化结论现在会输出实际 PASS / FAIL；分支保护脚本不再生成残缺请求体 / Fixed the CI gate templates so the structured verdict emits the actual PASS / FAIL value and the branch-protection script no longer produces a truncated request body
- 修复 Squad 路由：Bug Fix 会派发 Tester；软件开发中的接口测试用例与实现并行推进 / Fixed Squad routing so Bug Fix dispatches the Tester and API test cases advance in parallel with implementation
- 同步路线图中的 Skill 数量，并说明团队级审批应使用 CODEOWNERS 或 GitHub Rulesets / Synchronized the Skill count in the roadmap and clarified that team-level approval requires CODEOWNERS or GitHub Rulesets
- 调整项目定位表述，使真实任务验证状态与 ROADMAP 保持一致 / Aligned the project-positioning language with the real-task validation status in the ROADMAP

## v0.0.1 - 2026-08-15 · Initial release / 初始版本

历史演进（0.1.0–0.14.0）已压缩合并为本版本：一套可直接复制运行的 Multica 模板库。
Historical iterations (0.1.0–0.14.0) are condensed into this release: a copy-paste-ready Multica template library.

### Added / 新增

- **Agent 模板 / Agent templates**：6 个共享角色（Leader / Architect / FrontendDev / BackendDev / Tester / Reviewer），位于 `templates/zh_CN/agents/` 与 `templates/en_US/agents/`
- **Skill 模板 / Skill templates**：6 个共享 Skill（`multica-verification` 判门 / `multica-gate-setup` CI 硬门禁 / `multica-test-design` / `multica-requirement-analysis` / `multica-technical-design` / `multica-implementation`），统一 `multica-` 前缀，按名称挂载
- **Squad Starter / Squad starters**：`software-development`（推荐）与 `bug-fix`（实验性），各含 README / squad / issue 三件套
- **方法论 / Methodology**：`docs/` 5 篇（指令归属 / 门禁与证据 / 常见错误 / 裁剪扩展 / 命名规范）
- **CI 硬门禁 / CI hard gates**：`delivery-gate.yml` / `branch-protection.json` / `apply-branch-protection.sh` 随 `multica-gate-setup` skill 自包含
- **国际化 / i18n**：`README.md` ↔ `README.en.md` 顶部互挂切换链接；`templates/` 与 `docs/` 按 `zh_CN/` / `en_US/` 双目录存放；根文档（AGENTS / CHANGELOG / ROADMAP / SECURITY / CONTRIBUTING）单文件化并采用中英结合写法

### Changed / 变更

- 无（本版本为压缩合并后的初始版本）。No changes — this is the initial condensed release.
