# Apifox 用例补充 - 参考手册

**固定基地址**：`https://apifox.example.com`

---

## 常见错误

| 现象 | 原因 | 处理 |
|------|------|------|
| MCP 403 / project get 403 | 无项目权限或 ID 错 | 换有权限账号 Token 或核对项目 ID；**禁止**自动换其它项目继续 |
| MCP/CLI 401 | Token 无效 | `apifox auth login --api-base-url https://apifox.example.com` |
| MCP 403 | 无项目权限 | 换有权限账号 Token；禁止换项目硬写 |
| 连到 app.apifox.com | 基地址错误 | 使用私有化地址 |
| TLS 错误 | 自签证书 | 优先配置企业 CA；无法配置时显式 `APIFOX_INSECURE_TLS=1` |
| Automation caller branch required | 不能直写 main | 走 AI 分支 |
| create Invalid Parameter | 未 pick 接口 | `branch pick-to --endpoint-ids` |
| merge 422001 | main 未开 AI 写 | 客户端合并 |
| path 为 null | 局部 update | 用 `safe-update-case.js` |
| 「此响应已被删除」 | `responseId: ""` | 用 `responseId: 0` + `responseValidate: false` |
| 仍校验成功 200 | 只改 options 仍绑成功 ID | 负向必须 `responseId: 0` |
| 接口/项目找不到 | 名称含糊、未给 projectId、或非唯一匹配 | **停止生成**；引导用户补**数字项目 ID** / 接口 ID / path；拿到项目 ID 后 upsert；**禁止**臆造或换错项目硬写 |
| 环境对不上 | 用了其它项目或不符的 env | 在**当前已确认项目** `environment list` 核对；多候选/找不到则请用户给 env ID；确认后可写入登记表；禁止凑合实测 |
| 再次遇到同一系统却问项目 ID | 未查登记表 | 任务开始先 `systems-registry.js lookup --name <系统名>`；命中仍要 `project get` 复核 |
| 把指令里少数示例项目当全集 | 写死项目清单 | **禁止**；项目很多，只认用户输入 / 登记表 / 唯一按名匹配 |
| 同接口建了多个场景 | 把「扩充场景」理解成 create 多场景 | **同一接口只挂一个场景**；覆盖用场景内差异化步骤；误建的删除收拢 |
| 断言失败：根对象 include 数字 | `responseJson` path=`$.` + include `"1001001"` | 改用 `responseText include`，或 JSONPath 到字段/数组 |
| 脆快照全量 equal 失败 | 列表 body 整包快照 | 改为结构/关键字段断言，并用 `apifox run` 复跑 |

---

## 系统登记表

空模板：`.apifox/systems-registry.example.json`。运行时文件由 `systems-registry.js` 解析（**不含 Token**）。

```bash
node scripts/systems-registry.js path          # 查看实际读写路径
node scripts/systems-registry.js list
node scripts/systems-registry.js lookup --name "某系统"
node scripts/systems-registry.js upsert --name "某系统" --project-id 123 --project-name "某系统" --env-id 456 --env-name 测试环境
```

路径优先序：`APIFOX_SYSTEMS_REGISTRY` → `APIFOX_SKILL_STATE_DIR` → `<skill>/.apifox/`；若设了 `APIFOX_OPERATOR` / `APIFOX_USER_EMAIL`，文件名为 `systems-registry.<operator>.json` 以隔离多人。

项目 ID 合法来源：用户本轮给出 → 登记 **精确** lookup → `project list` 唯一按名命中；否则停并索要数字项目 ID。`project get` 通过后必须 upsert。**禁止胡编、猜测、模糊匹配；禁止把个人登记表打进共享 Skill 分发。**

环境名称因项目而异（SIT / 测试环境 / …），只在当前项目 list 后精确匹配或问用户。

## 实测响应与断言模板

### 采样建议（curl）

```bash
# 1) 按项目方式取 Cookie / Token（与发现的鉴权一致）
# 2) 带 Cookie 调业务接口
curl.exe -sk --max-time 15 -X POST "$BASE$path" \
  -H "Content-Type: application/json" -H "Accept: application/json" \
  -H "Cookie: $COOKIE" --data-binary "@body.json" -D headers.txt -o body.out -w "HTTP:%{http_code}\n"
```

### 成功响应（示例）

```json
{ "subjectId": 39, "milestoneId": 209, "fileId": 342, "fileGroupId": "...", "versionNo": 77 }
```

| 字段 | 级别 | 断言 |
|------|------|------|
| httpCode | 硬 | equal `200` |
| subjectId / milestoneId / fileGroupId 等稳定业务键 | 硬 | equal 请求期望值 |
| fileId / versionNo 等易变键 | 软 | exists |

### 业务错误（示例）

```json
{
  "success": false,
  "errorCode": "31100004",
  "errorMessage": "Feature field[subjectId] can't be null",
  "data": null
}
```

| 断言 | 示例 |
|------|------|
| httpCode | equal `400` |
| $.success | equal `false` |
| $.errorCode | equal `31100004` 或 `31100005` |
| $.errorMessage | include 字段名或 `not found` |
| $.fileId | notExist（若适用） |

### 校验响应开关

| 用例类型 | responseId | options.responseValidate |
|----------|------------|--------------------------|
| 正向 / 边界成功 | 接口「成功」响应定义 ID | true（或不写，默认开） |
| 非 200 负向 | `0` | `false` |

> 本 Skill **不生成未鉴权用例**。

---

## 场景设计与条数（禁止胡编）

**条数 = 场景证据表中「需补充」的行数**，不设固定上/下限。

### 证据来源（任一条即可，须可追溯）

1. Apifox 接口定义：必填、类型、枚举、说明、已有响应/错误示例  
2. 需求/备注/同模块已知 errorCode 习惯  
3. **目标环境实测**（优先用于断言与「是否真校验」）  
4. 同接口已有用例（用于比对缺口，避免重复）

### 常见误区

| 错误做法 | 正确做法 |
|----------|----------|
| 每个接口都造 10 条 | 参数少可以 2～3 条；复杂接口按分支加到够覆 |
| 套用「替换课题文件」示例清单 | 仅参考结构，重写 `caseSpecs` |
| 未测就断言「无效 xxx 必失败」 | 先实测；仍 200 则按成功或删该负向 |
| 为「安全维度完整」加未鉴权 | 本 Skill 明确不做 |
| 选填字段无依据也逐个缺参 | 仅对**必填或实测会报错**的字段做缺参 |

### `caseSpecs` 与生成

`generate-cases.js` **只**读 `caseSpecs`，没有默认清单。示例见 `config.example.json`（单接口样例，可增删）。

每条必须包含：

- `expected.statusCode`、`expected.responseValidate`
- `evidence.scenario.type/source/summary`
- `evidence.probe.environmentId/observedAt/statusCode/responseSummary`
- `sideEffect.level/testData/cleanup`

`expected.statusCode` 必须与实测状态码一致。证据缺失、环境不一致、重复名称或文件名时生成器直接失败。

### 环境和副作用

- `targetEnvironment.type` 必须为 `non-production`
- `write/destructive` 场景使用专用测试数据，并提供可执行清理说明
- 默认禁止生产环境实测
- 无法安全清理的操作先请用户确认，不以“覆盖完整”为由直接执行

---

## Processor 要点

- `requestBody.data` 存 JSON 字符串（不是 rawData）
- 断言：`assertion` + `equal` + `responseJson`
- 鉴权：`commonScript`，ID 来自同模块发现
- update：**禁止**只传 `preProcessors`

---

## get→改→update（安全更新）

```bash
node scripts/safe-update-case.js \
  --project $APIFOX_PROJECT_ID \
  --branch <AI_BRANCH> \
  --case-id 3557005 \
  --patch patch.json
```

`patch.json` 示例：

```json
{
  "preProcessors": [ ... ],
  "postProcessors": [ ... ],
  "responseId": 0,
  "options": { "responseValidate": false }
}
```

脚本仅允许 `ai/` 分支，禁止 patch 修改 `path/method/apiDetailId`；写入后逐项比对这三个不可变字段。

---

## 鉴权发现 CLI

```bash
set APIFOX_PROJECT_ID=<当前项目数字ID>
set APIFOX_ENDPOINT_ID=<当前接口数字ID>
set APIFOX_SOURCE_BRANCH=main
set APIFOX_OPERATOR=<操作者简称>
node scripts/discover-auth.js
# 输出：auth-discovery.json（含来源、候选、confidence、requiresConfirmation）
```

只有同接口/同模块历史步骤且脚本 ID 在当前项目可验证时，才可自动推荐。跨模块、脚本库关键词、其它项目残留 ID 禁止自动采用。
写入 config 时必须同时记录：

```json
"authDiscovery": {
  "source": "target-scenario-same-endpoint / same-endpoint / ...",
  "projectId": "<当前项目>",
  "moduleId": "<目标接口 moduleId>",
  "confidence": "high|medium|low",
  "confirmed": true,
  "validatedScripts": [{ "id": 123, "name": "从 common-script 解析到的真实名" }]
}
```

非 `high` 结果必须 `confirmed: true`。示例 config 里的脚本 ID 只是占位，禁止照搬。

---

## AI 分支策略与命名

分两种场景，**不可混用规则**：

### A · OpenAPI 同步（Backend，`sync_openapi.js`）

| 规则 | 说明 |
| --- | --- |
| **每次同步新建分支** | 每次发布/变更 `openapi.json` 并同步 → `branch create` 新 AI 分支 |
| **命名** | `ai/<ISSUE-KEY>-openapi-<YYYYMMDD>`；同日多次 `-r2`、`-r3` |
| **禁止** | 直写 `main`；复用已 merge 的旧 openapi 分支 |
| **细节** | 见 [`openapi-branch-workflow.md`](openapi-branch-workflow.md) |

### B · 场景用例补充（Tester T1 / Apifox 脚本）

**默认同 Issue 内复用**同一 AI 分支做 `pick-to` + 追加步骤；只有用户明确要求「新建 / 多个 AI 分支」时才额外 create。

解析顺序：`APIFOX_AI_BRANCH` / config `aiBranch` → 本 Issue 的 `ai/<ISSUE-KEY>-openapi-*`（Backend 已建则优先 pick）→ 项目已有未归档工作分支 → 皆无则 create 一次。

首次创建命名（仅场景、且尚无 openapi 分支时）：

```
ai/<ISSUE-KEY>-scenarios-<YYYYMMDD>
```

或历史格式：`ai/YYYYMMDD-from-main-<模块简称>`

后续接口只在该分支 `pick-to` + 写入，不要再 `branch create`（OpenAPI 同步除外，见 §A）。

---

## 场景挂载（主交付）

历史自动化在「场景用例」目录树。补充用例必须导入场景，不能只停在单接口用例。

### 同一接口只挂一个场景（强制）

```
扩充覆盖 = 同场景追加差异化步骤
禁止      = 为同一 endpoint 再 create 「主流程 / 经典产品 / 多语言」等多个场景
例外      = 用户明确要求拆多个场景；或历史已约定且入参/造数链路必须独立的多场景
```

用户说「扩充场景 / 补充测试场景」时，默认按**加步骤**理解，不要新建场景。

### 发现目标

```bash
node scripts/discover-scenario-target.js
# recommended.folderId / scenarioId / scenarioName → 写入 config.scenarioTarget
# selfHit=true → mode 必须为 append-existing
```

### 导入步骤

优先：

```bash
# 先 batch-create 得到 manifest.json
node scripts/append-to-scenario.js --branch <AI_BRANCH> --endpoint-id <ID> --manifest <dir>/manifest.json --apply
```

等价 CLI：

```bash
apifox test-scenario import-steps <SCENARIO_ID> --project $APIFOX_PROJECT_ID --branch <AI_BRANCH> \
  --source test-case --endpoint <ENDPOINT_ID> --ids <CASE_IDS> --sync manual \
  --api-base-url https://apifox.example.com
```

规则：

1. 有同接口历史场景 → **只**追加到该场景  
2. 同接口尚无场景时，才在同模块历史 `folderId` 下**新建一个**「`<接口名>`」或「`<接口名>-自动化补充`」  
3. 无目录 → 停，请用户指定  
4. AI 分支须 `pick-to --test-scenario-ids` 或 `--test-scenario-folder-ids`  
5. 场景内已绑定同一 test-case / 等价步骤 → skip  
6. 误建的同接口多余场景应删除并收拢步骤到唯一场景（用户要求保留除外）  

### 断言反踩坑（WS-40）

| 错误做法 | 正确做法 |
|----------|----------|
| 整包 `responseJson equal` 全量列表 body | 结构断言：`code`、`isNotEmpty`/`exists`、关键业务字段 |
| `responseJson` + path=`$.` + `include` + `"1001001"` | 用 `responseText include`，或 JSONPath 到数组/字段后再断言 |
| JSONPath 过滤结果是数组却 `equal` 标量 | 改为 `include`，或取下标 / 改路径；以 `apifox run` 实测为准 |
| 同场景重复 append 近似断言步骤 | skip / 合并；一步覆盖一个差异化维度即可 |

---

## 幂等与命名

- 单接口：`test-case list --endpoint`，名称已存在 → skip  
- 场景：已绑定相同 caseId 的步骤 → skip  
- 前缀：`APIFOX_CASE_NAME_PREFIX` 或接口名  

---

## 用户手动合并

1. 切到 AI 分支审查场景步骤是否与历史同目录  
2. 合并到 main  
3. **必须勾选场景用例**（`--test-scenario-ids`）  
4. 建议同时勾选对应 `--test-case-ids`  
5. **不要**只勾单接口测试用例（会和历史场景树分离）  
6. **不要**勾选 endpoint / 响应定义  
7. CLI 示例（仅用户明确要求时）：

```bash
apifox branch merge --project $APIFOX_PROJECT_ID --type ai \
  --from <AI_BRANCH> --to main \
  --test-scenario-ids <SCENARIO_ID> \
  --test-case-ids <CASE_IDS>
```

---

## MCP mcp.json（Windows）

```json
{
  "mcpServers": {
    "apifox": {
      "command": "cmd",
      "args": ["/c", "npx", "-y", "apifox-mcp-server@latest", "--project-id=YOUR_PROJECT_ID"],
      "env": {
        "APIFOX_ACCESS_TOKEN": "YOUR_TOKEN",
        "APIFOX_API_BASE_URL": "https://apifox.example.com",
        "NODE_EXTRA_CA_CERTS": "C:\\path\\to\\company-ca.pem"
      }
    }
  }
}
```

脚本侧仅在无法配置企业 CA 时使用 `APIFOX_INSECURE_TLS=1`；它会显式关闭 TLS 校验并打印警告。Token 只放环境变量或凭据存储，不得放入 `config.json`。
