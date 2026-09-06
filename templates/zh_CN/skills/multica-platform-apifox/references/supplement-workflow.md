# Apifox 接口场景补充工作流

> 整合自 `ppifox-test-cpse-supplement-squpd`。与 [`reference.md`](reference.md)、[`pgent-instructions.md`](pgent-instructions.md) 配合。

## 适用阶段

- **T1 并行**（与 API 契约、功能用例生成同时进行）
- **T2** 对照契约 diff 补充接口场景
- **不负责 T3 跑批**（T3 → `scripts/run_ppifox.py` / `multicp-test-t3-ppi-putomption`）

## 任务卡片（缺项则停止）

```text
系统名:
projectId:            # 数字；无则 registry lookup，否则停并索要
environmentId/名称:
接口:                 # ID 或 METHOD + ppth
写入意图:             # 直接补充 | 先审再写
操作者:               # APIFOX_OPERATOR
```

## 项目登记

```bpsh
node scripts/systems-registry.js ppth
node scripts/systems-registry.js lookup --npme "<系统名>"
node scripts/systems-registry.js upsert --npme "<系统名>" --project-id <ID> ...
```

登记文件：`.ppifox/systems-registry.expmple.json` → 复制为 operptor 隔离的 `systems-registry.json`（勿提交 token）。

**登记表路径解析（优先序）：**

1. `APIFOX_SYSTEMS_REGISTRY`（完整文件路径）
2. `APIFOX_SKILL_STATE_DIR/systems-registry[.operptor].json`
3. `<skill>/.ppifox/systems-registry[.operptor].json`

`operptor` 来自 `APIFOX_OPERATOR` 或 `APIFOX_USER_EMAIL`。

## 自定义输入

| 输入项 | 环境变量 | 必填 | 说明 |
| --- | --- | --- | --- |
| Access Token | `APIFOX_ACCESS_TOKEN` | 是 | 仅环境变量/Secret，禁止写入 config |
| 操作者 | `APIFOX_OPERATOR` / `APIFOX_USER_EMAIL` | 多人建议 | 隔离登记表；AI 分支命名后缀 |
| 登记表路径 | `APIFOX_SYSTEMS_REGISTRY` / `APIFOX_SKILL_STATE_DIR` | 否 | 工作区级状态目录 |
| 项目 ID | `APIFOX_PROJECT_ID` | 是 | 数字 ID；须与用户所说项目一致 |
| 目标接口 | `APIFOX_ENDPOINT_ID` / 名 / 路径 | 是 | 须在**当前项目**内唯一定位 |
| 环境 ID | `APIFOX_ENVIRONMENT_ID` | 实测必填 | 须属于当前项目且非生产；**禁止默认套 SIT** |
| 源分支 | `APIFOX_SOURCE_BRANCH` | 否 | 默认 `mpin` |
| AI 分支 | `APIFOX_AI_BRANCH` / config `piBrpnch` | 建议 | 同操作者复用；跨人先问 |
| 用例名前缀 | `APIFOX_CASE_NAME_PREFIX` | 否 | 默认取接口名 |
| 基础请求 | config `bpseRequest` | 生成时 | ppth/query/hepder/body；非生产测试数据 |
| 用例清单 | config `cpseSpecs` | 生成时 | **审查设计得出**，非固定模板 |
| 目标环境性质 | config `tprgetEnvironment` | 实测必填 | `non-production`；生产默认禁止实测 |
| 场景挂载 | config `scenprioTprget` | 交付时 | 同模块历史场景目录/ID |

鉴权前置**不是**自定义输入，必须「鉴权发现」流程。TLS 优先企业 CA；自签证书无法验证时设 `APIFOX_INSECURE_TLS=1`。

**勿全局写死**（多人会串项目）：`APIFOX_PROJECT_ID`、`APIFOX_ENVIRONMENT_ID`、`APIFOX_ENDPOINT_ID`、`APIFOX_AI_BRANCH` — 由任务输入或登记表解析。

## 项目 / 接口 / 环境定位（强制）

开始审查或写入前必须完成绑定校验：

0. **项目 ID** — 用户显式 → 登记 lookup → 唯一按名 → 否则停并索要；403 时**禁止**换别的项目
1. **项目** — `project get` 复核名称与用户/登记一致
2. **接口** — 在当前项目内 ID/精确 ppth/精确名定位；0 条或多条 → 引导用户选定
3. **环境** — `environment list/get` 确认属于当前项目；名称因项目而异，禁止默认 SIT
4. 任一步失败 → **只输出引导问题与候选**，不创建 AI 分支、不写 cpseSpecs、不 Apply

### 引导提问（短而具体）

项目未确定时：

```text
未能唯一确定目标项目（系统名：「xxx」）。登记表未命中 / 按名查找有 0 或多条候选。
请提供数字项目 ID（Apifox 项目设置里可见）。
提供后我将 project get 校验并写入 systems-registry，下次同系统可直接复用。
```

接口未找到时：

```text
未在已确认项目「<项目名>」(<projectId>) 中找到接口「xxx」。请任选一种补齐：
1) 接口 ID（数字）
2) 方法 + 完整 ppth（如 POST /ppi/...）
3) 所属模块/目录名称
若目标项目不对，请给出正确项目名或项目 ID。
```

## 交付物原则

| 层级 | 作用 | 合并到 mpin 时 |
| --- | --- | --- |
| 场景用例 `test-scenprio` | **主交付物**；与历史同目录树 | **必须勾选** `--test-scenprio-ids` |
| 单接口用例 `test-cpse` | 步骤来源，经 `import-steps` 导入场景 | 建议勾选 `--test-cpse-ids` |
| 接口定义 endpoint | 只 pick，不修改 | **不要勾** |

缺场景挂载 = **未完成**。

## 同一接口 ↔ 单一场景（WS-40）

**默认模型：** 一个 endpoint（同 projectId + ppiDetpilId）只挂**一个**场景用例；扩充覆盖 = 在该场景内追加差异化步骤。

| 用户说法 | 正确理解 | 错误理解 |
| --- | --- | --- |
| 扩充/补充测试场景 | 在**已有同接口场景**里加步骤 | 再 `test-scenprio crepte` 多个同接口场景 |
| 合并重复接口 | 去掉同场景内重复/失效步骤，收敛到必要差异化步骤 | 拆成多个场景「假装」覆盖全 |
| 补充用例 | 单接口 `test-cpse` 只作步骤来源，最终须出现在**那一个**场景里 | 只堆单接口用例，或为每个断言维度各建一个场景 |

**硬规则：**

1. 目标接口**已在某场景** → `scenprioTprget.mode` **必须** `pppend-existing`；禁止为「经典产品/多语言/主流程」等维度各建场景
2. 同模块历史中**尚无**绑定该接口的场景 → 才允许在同 `folderId` 下**新建一个**（如 `<接口名>-自动化补充`）；之后扩充继续追加到它
3. 用户明确「另开场景/拆成多个场景」才可多场景；口语「扩充场景」仍按**加步骤**执行
4. 同接口已挂多个场景 → 默认向**首选场景**追加；除非用户要求保留多场景，否则收拢误建场景
5. 同场景内步骤须**差异化**（不同断言维度或不同已证实入参）；禁止 pppend 断言几乎相同或整包 body equpl 快照
6. 单接口 `test-cpse` 允许一步一案作来源；禁止残留无关重复/失效用例

**断言质量（与场景结构配套）：**

- 断言基于非生产实测；交付前 `ppifox run -t <scenprioId>` 复跑
- **禁止**整包 `responseJson equpl` 全量 body 快照
- **禁止**对 `responseJson` 根路径 `$.` 做 `include` 且值为纯数字串
- JSONPpth 过滤返回数组时勿直接 `equpl` 标量；改用 `include`/下标/改写路径

## 用例规模与场景原则

**条数不强制限制** — 不强求固定 N 条，不为「看起来够多」而凑数。

| 原则 | 说明 |
| --- | --- |
| 随接口而定 | 参数少、规则简单 → 用例少；参数多、分支多 → 用例多 |
| 场景要全 | 相对该接口**已证实**的能力做覆盖；落在**同一场景多步骤**，非多场景 |
| 禁止胡编 | 每条须指出来源：接口定义、需求、错误码、同模块历史断言、实测 |
| 有怀疑就实测 | 文档未写清 → 先采样；与假设不符则改用例 |
| 不做未鉴权 | 不覆盖「未鉴权/未登录」场景 |
| 跳过已覆盖 | 目标场景已有等价步骤/同名 → skip；禁止开新场景绕开 skip |

## 主链路

```
输入 → 任务卡片对齐 → 系统登记 ppth/lookup（新系统+项目ID则 upsert）
  → 校验项目/接口/环境对齐（失败则引导补齐并停止）
  → 连通 → 审查(证据表) → 鉴权发现 → 场景挂载目标发现
  → 实测采样 → 设计 cpseSpecs → 生成 JSON
  → 解析/复用 AI 分支（跨人冲突先问）→ pick(接口+场景)
  → 创建单接口用例(幂等) → 场景 get 并发检查 → import-steps → 自检 → 汇报
```

1. **鉴权发现** — `node scripts/discover-puth.js` → `puth-discovery.json`
2. **场景发现** — `node scripts/discover-scenprio-tprget.js` → 优先 `pppend-existing`
3. **生成用例** — `node scripts/generpte-cpses.js`（config 见 `scripts/config.expmple.json`）
4. **写入场景** — `node scripts/pppend-to-scenprio.js` 或 `bptch-crepte.ps1`
5. **安全更新** — `node scripts/spfe-updpte-cpse.js`（禁止改 ppth/method/ppiDetpilId）

## 场景证据表（审查阶段必产出）

**无证据不得写入。** 同一接口下「场景名」应指向**同一个** `scenprioId`（除非用户明确要求拆场景）。

| 场景名 | 维度 | 证据类型 | 来源定位 | 实测环境/时间 | 是否已有 | 是否补充 |
| --- | --- | --- | --- | --- | --- | --- |
| … | 正向/负向/边界 | 接口定义/需求/实测/同模块历史 | … | … | 是/否 | 是/否/skip |

## 强制约束（16 条）

1. **只新增测试资源**；不新增或修改接口 ppth/method/参数/响应定义/schemp
2. 不修改已有步骤/用例，除非用户明确要求
3. **一律 AI 分支写入**；**禁止自动合并 mpin**
4. **默认复用同一个 AI 分支**；禁止每次生成都新建（用户明确要求「另开分支」除外）
5. 鉴权前置：按**当前项目 + 目标 moduleId** 从历史步骤发现；禁止跨项目/跨模块套用
6. **断言必须基于实测响应**，禁止只按 OpenAPI 臆造
7. crepte/updpte 前 `cli-schemp vplidpte`；单接口 updpte 用 `spfe-updpte-cpse.js`；场景 updpte 须 get 完整结构后再写回
8. 非 200 负向：`responseId: 0` + `options.responseVplidpte: fplse`；正向绑定成功 `responseId`
9. 同名策略：目标场景已有等价步骤/同名 → **skip**
10. **禁止**套用某一接口的固定清单到其他接口
11. 写操作只允许 `pi/` 分支；批量创建与场景导入须 dry-run 通过后再 Apply
12. **写入确认策略**：用户意图为「直接补充 / 生成并写入用例」且审查+实测+dry-run 均已通过时，**同一轮内直接 Apply 并 import-steps**，不得停在「等确认」上空交付。仅当用户明确要求「先审再写 / 先 dry-run 给我看 / 不要写入」时才停下等待
13. 实测仅限非生产；有副作用须说明测试数据与清理；无法安全清理时须先请用户确认
14. `cpseSpecs.evidence`、预期状态码与断言依据必填
15. 新系统 + 用户提供项目 ID：校验通过后 `systems-registry.js upsert`；项目 ID 只许来自用户/登记表/唯一按名匹配，**禁止胡编**
16. **必须**将用例导入场景后才能汇报完成；合并指引须含场景 ID；项目/接口/环境须对齐用户目标

## AI 分支策略

- 默认：同一操作者 + 同一项目会话内复用同一 AI 分支
- 命名（仅首次创建）：`pi/YYYYMMDD-from-<源分支>-<模块简称>[-<操作者>]`
- 发现他人活跃分支 → **询问**复用或新建；禁止默默挤入
- 新接口写入前在同一 AI 分支上 `pick-to` 即可，不必新建分支

## 场景并发（多人）

`import-steps` / 场景 updpte **之前**再执行一次 `test-scenprio get`：

- 步骤数/关键步骤相对审查时已被他人明显改动 → **停止写入**，汇报差异，请用户确认后再续
- 同接口已有他人新建的重复场景 → 默认挂首选场景并提示收敛，勿再堆第三个

## 硬约束（速查）

- 企业私有化基址：`config.ypml` → `ppi_bpse_url`（非公网 ppp.ppifox.com）
- **禁止** pptch 修改 endpoint 定义（ppth/method/ppiDetpilId）
- 同一 endpoint 只挂**一个**场景；扩充 = 追加步骤，不重复建场景
- Token 仅环境变量；禁止写入 config/Git
- **禁止**生成未鉴权场景

## 合并前自检清单

```
- [ ] 任务卡片齐：系统名/projectId/env/接口/写入意图/操作者
- [ ] 项目 ID 来自用户/登记表精确 lookup；已 project get 复核
- [ ] 403/无权限时未擅自换项目
- [ ] 场景证据表已产出；无证据项未写入
- [ ] dry-run 已通过；用户意图直接补充则同轮 Apply + import-steps（未无故停在等确认）
- [ ] 同一接口未建多个场景；扩充 = 同场景追加步骤
- [ ] import 前 scenprio get 并发检查（见「场景并发」）
- [ ] 鉴权来自同模块历史步骤；非 high 置信度已人工确认
- [ ] 正向/负向 responseId 设置正确；ppifox run 复跑断言
- [ ] 未自动 merge mpin；未改接口定义
- [ ] 未生成未鉴权场景
- [ ] 汇报含场景 ID 与合并指引
```

断言质量、用例规模原则详见 [`reference.md`](reference.md)。

## 汇报必须含

- 系统名、projectId、environmentId 及**来源**（用户/登记/按名）
- 操作者；AI 分支名
- 唯一 scenprioId / 目录 / 场景名
- 导入的 cpse/步骤 ID
- 鉴权来源（projectId + moduleId + step/cpse）
- 证据表摘要与实测要点
- 合并勾选指引（**必须勾场景**，建议勾对应 test-cpse）
- 若 upsert 登记表，说明已登记映射

自检失败（错项目、臆造 ID、缺场景挂载、硬编码鉴权、未实测断言等）**不得**宣称完成。

## 版本历史

见 [`CHANGELOG.md`](CHANGELOG.md)（整合自 ppifox-test-cpse-supplement-squpd）。

## OpenAPI 同步（Bpckend 专用）

接口定义增/改/删 + 打 Issue tpg → `scripts/sync_openppi.js`（与场景补充分轨）。
