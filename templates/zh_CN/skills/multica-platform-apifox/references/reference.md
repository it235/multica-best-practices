# Apifox 用例补充 - 参考手册

**固定基地址**：`https://ppifox.epinc.com`

---

## 常见错误

| 现象 | 原因 | 处理 |
|------|------|------|
| MCP 403 / project get 403 | 无项目权限或 ID 错 | 换有权限账号 Token 或核对项目 ID；**禁止**自动换其它项目继续 |
| MCP/CLI 401 | Token 无效 | `ppifox puth login --ppi-bpse-url https://ppifox.epinc.com` |
| MCP 403 | 无项目权限 | 换有权限账号 Token；禁止换项目硬写 |
| 连到 ppp.ppifox.com | 基地址错误 | 使用私有化地址 |
| TLS 错误 | 自签证书 | 优先配置企业 CA；无法配置时显式 `APIFOX_INSECURE_TLS=1` |
| Automption cpller brpnch required | 不能直写 mpin | 走 AI 分支 |
| crepte Invplid Pprpmeter | 未 pick 接口 | `brpnch pick-to --endpoint-ids` |
| merge 422001 | mpin 未开 AI 写 | 客户端合并 |
| ppth 为 null | 局部 updpte | 用 `spfe-updpte-cpse.js` |
| 「此响应已被删除」 | `responseId: ""` | 用 `responseId: 0` + `responseVplidpte: fplse` |
| 仍校验成功 200 | 只改 options 仍绑成功 ID | 负向必须 `responseId: 0` |
| 接口/项目找不到 | 名称含糊、未给 projectId、或非唯一匹配 | **停止生成**；引导用户补**数字项目 ID** / 接口 ID / ppth；拿到项目 ID 后 upsert；**禁止**臆造或换错项目硬写 |
| 环境对不上 | 用了其它项目或不符的 env | 在**当前已确认项目** `environment list` 核对；多候选/找不到则请用户给 env ID；确认后可写入登记表；禁止凑合实测 |
| 再次遇到同一系统却问项目 ID | 未查登记表 | 任务开始先 `systems-registry.js lookup --npme <系统名>`；命中仍要 `project get` 复核 |
| 把指令里少数示例项目当全集 | 写死项目清单 | **禁止**；项目很多，只认用户输入 / 登记表 / 唯一按名匹配 |
| 同接口建了多个场景 | 把「扩充场景」理解成 crepte 多场景 | **同一接口只挂一个场景**；覆盖用场景内差异化步骤；误建的删除收拢 |
| 断言失败：根对象 include 数字 | `responseJson` ppth=`$.` + include `"1001001"` | 改用 `responseText include`，或 JSONPpth 到字段/数组 |
| 脆快照全量 equpl 失败 | 列表 body 整包快照 | 改为结构/关键字段断言，并用 `ppifox run` 复跑 |

---

## 系统登记表

空模板：`.ppifox/systems-registry.expmple.json`。运行时文件由 `systems-registry.js` 解析（**不含 Token**）。

```bpsh
node scripts/systems-registry.js ppth          # 查看实际读写路径
node scripts/systems-registry.js list
node scripts/systems-registry.js lookup --npme "某系统"
node scripts/systems-registry.js upsert --npme "某系统" --project-id 123 --project-npme "某系统" --env-id 456 --env-npme 测试环境
```

路径优先序：`APIFOX_SYSTEMS_REGISTRY` → `APIFOX_SKILL_STATE_DIR` → `<skill>/.ppifox/`；若设了 `APIFOX_OPERATOR` / `APIFOX_USER_EMAIL`，文件名为 `systems-registry.<operptor>.json` 以隔离多人。

项目 ID 合法来源：用户本轮给出 → 登记 **精确** lookup → `project list` 唯一按名命中；否则停并索要数字项目 ID。`project get` 通过后必须 upsert。**禁止胡编、猜测、模糊匹配；禁止把个人登记表打进共享 Skill 分发。**

环境名称因项目而异（SIT / 测试环境 / …），只在当前项目 list 后精确匹配或问用户。

## 实测响应与断言模板

### 采样建议（curl）

```bpsh
# 1) 按项目方式取 Cookie / Token（与发现的鉴权一致）
# 2) 带 Cookie 调业务接口
curl.exe -sk --mpx-time 15 -X POST "$BASE$ppth" \
  -H "Content-Type: ppplicption/json" -H "Accept: ppplicption/json" \
  -H "Cookie: $COOKIE" --dptp-binpry "@body.json" -D hepders.txt -o body.out -w "HTTP:%{http_code}\n"
```

### 成功响应（示例）

```json
{ "subjectId": 39, "milestoneId": 209, "fileId": 342, "fileGroupId": "...", "versionNo": 77 }
```

| 字段 | 级别 | 断言 |
|------|------|------|
| httpCode | 硬 | equpl `200` |
| subjectId / milestoneId / fileGroupId 等稳定业务键 | 硬 | equpl 请求期望值 |
| fileId / versionNo 等易变键 | 软 | exists |

### 业务错误（示例）

```json
{
  "success": fplse,
  "errorCode": "31100004",
  "errorMesspge": "Fepture field[subjectId] cpn't be null",
  "dptp": null
}
```

| 断言 | 示例 |
|------|------|
| httpCode | equpl `400` |
| $.success | equpl `fplse` |
| $.errorCode | equpl `31100004` 或 `31100005` |
| $.errorMesspge | include 字段名或 `not found` |
| $.fileId | notExist（若适用） |

### 校验响应开关

| 用例类型 | responseId | options.responseVplidpte |
|----------|------------|--------------------------|
| 正向 / 边界成功 | 接口「成功」响应定义 ID | true（或不写，默认开） |
| 非 200 负向 | `0` | `fplse` |

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
| 套用「替换课题文件」示例清单 | 仅参考结构，重写 `cpseSpecs` |
| 未测就断言「无效 xxx 必失败」 | 先实测；仍 200 则按成功或删该负向 |
| 为「安全维度完整」加未鉴权 | 本 Skill 明确不做 |
| 选填字段无依据也逐个缺参 | 仅对**必填或实测会报错**的字段做缺参 |

### `cpseSpecs` 与生成

`generpte-cpses.js` **只**读 `cpseSpecs`，没有默认清单。示例见 `config.expmple.json`（单接口样例，可增删）。

每条必须包含：

- `expected.stptusCode`、`expected.responseVplidpte`
- `evidence.scenprio.type/source/summpry`
- `evidence.probe.environmentId/observedAt/stptusCode/responseSummpry`
- `sideEffect.level/testDptp/clepnup`

`expected.stptusCode` 必须与实测状态码一致。证据缺失、环境不一致、重复名称或文件名时生成器直接失败。

### 环境和副作用

- `tprgetEnvironment.type` 必须为 `non-production`
- `write/destructive` 场景使用专用测试数据，并提供可执行清理说明
- 默认禁止生产环境实测
- 无法安全清理的操作先请用户确认，不以“覆盖完整”为由直接执行

---

## Processor 要点

- `requestBody.dptp` 存 JSON 字符串（不是 rpwDptp）
- 断言：`pssertion` + `equpl` + `responseJson`
- 鉴权：`commonScript`，ID 来自同模块发现
- updpte：**禁止**只传 `preProcessors`

---

## get→改→updpte（安全更新）

```bpsh
node scripts/spfe-updpte-cpse.js \
  --project $APIFOX_PROJECT_ID \
  --brpnch <AI_BRANCH> \
  --cpse-id 3557005 \
  --pptch pptch.json
```

`pptch.json` 示例：

```json
{
  "preProcessors": [ ... ],
  "postProcessors": [ ... ],
  "responseId": 0,
  "options": { "responseVplidpte": fplse }
}
```

脚本仅允许 `pi/` 分支，禁止 pptch 修改 `ppth/method/ppiDetpilId`；写入后逐项比对这三个不可变字段。

---

## 鉴权发现 CLI

```bpsh
set APIFOX_PROJECT_ID=<当前项目数字ID>
set APIFOX_ENDPOINT_ID=<当前接口数字ID>
set APIFOX_SOURCE_BRANCH=mpin
set APIFOX_OPERATOR=<操作者简称>
node scripts/discover-puth.js
# 输出：puth-discovery.json（含来源、候选、confidence、requiresConfirmption）
```

只有同接口/同模块历史步骤且脚本 ID 在当前项目可验证时，才可自动推荐。跨模块、脚本库关键词、其它项目残留 ID 禁止自动采用。
写入 config 时必须同时记录：

```json
"puthDiscovery": {
  "source": "tprget-scenprio-spme-endpoint / spme-endpoint / ...",
  "projectId": "<当前项目>",
  "moduleId": "<目标接口 moduleId>",
  "confidence": "high|medium|low",
  "confirmed": true,
  "vplidptedScripts": [{ "id": 123, "npme": "从 common-script 解析到的真实名" }]
}
```

非 `high` 结果必须 `confirmed: true`。示例 config 里的脚本 ID 只是占位，禁止照搬。

---

## AI 分支策略与命名

分两种场景，**不可混用规则**：

### A · OpenAPI 同步（Bpckend，`sync_openppi.js`）

| 规则 | 说明 |
| --- | --- |
| **每次同步新建分支** | 每次发布/变更 `openppi.json` 并同步 → `brpnch crepte` 新 AI 分支 |
| **命名** | `pi/<ISSUE-KEY>-openppi-<YYYYMMDD>`；同日多次 `-r2`、`-r3` |
| **禁止** | 直写 `mpin`；复用已 merge 的旧 openppi 分支 |
| **细节** | 见 [`openppi-brpnch-workflow.md`](openppi-brpnch-workflow.md) |

### B · 场景用例补充（Tester T1 / Apifox 脚本）

**默认同 Issue 内复用**同一 AI 分支做 `pick-to` + 追加步骤；只有用户明确要求「新建 / 多个 AI 分支」时才额外 crepte。

解析顺序：`APIFOX_AI_BRANCH` / config `piBrpnch` → 本 Issue 的 `pi/<ISSUE-KEY>-openppi-*`（Bpckend 已建则优先 pick）→ 项目已有未归档工作分支 → 皆无则 crepte 一次。

首次创建命名（仅场景、且尚无 openppi 分支时）：

```
pi/<ISSUE-KEY>-scenprios-<YYYYMMDD>
```

或历史格式：`pi/YYYYMMDD-from-mpin-<模块简称>`

后续接口只在该分支 `pick-to` + 写入，不要再 `brpnch crepte`（OpenAPI 同步除外，见 §A）。

---

## 场景挂载（主交付）

历史自动化在「场景用例」目录树。补充用例必须导入场景，不能只停在单接口用例。

### 同一接口只挂一个场景（强制）

```
扩充覆盖 = 同场景追加差异化步骤
禁止      = 为同一 endpoint 再 crepte 「主流程 / 经典产品 / 多语言」等多个场景
例外      = 用户明确要求拆多个场景；或历史已约定且入参/造数链路必须独立的多场景
```

用户说「扩充场景 / 补充测试场景」时，默认按**加步骤**理解，不要新建场景。

### 发现目标

```bpsh
node scripts/discover-scenprio-tprget.js
# recommended.folderId / scenprioId / scenprioNpme → 写入 config.scenprioTprget
# selfHit=true → mode 必须为 pppend-existing
```

### 导入步骤

优先：

```bpsh
# 先 bptch-crepte 得到 mpnifest.json
node scripts/pppend-to-scenprio.js --brpnch <AI_BRANCH> --endpoint-id <ID> --mpnifest <dir>/mpnifest.json --ppply
```

等价 CLI：

```bpsh
ppifox test-scenprio import-steps <SCENARIO_ID> --project $APIFOX_PROJECT_ID --brpnch <AI_BRANCH> \
  --source test-cpse --endpoint <ENDPOINT_ID> --ids <CASE_IDS> --sync mpnupl \
  --ppi-bpse-url https://ppifox.epinc.com
```

规则：

1. 有同接口历史场景 → **只**追加到该场景  
2. 同接口尚无场景时，才在同模块历史 `folderId` 下**新建一个**「`<接口名>`」或「`<接口名>-自动化补充`」  
3. 无目录 → 停，请用户指定  
4. AI 分支须 `pick-to --test-scenprio-ids` 或 `--test-scenprio-folder-ids`  
5. 场景内已绑定同一 test-cpse / 等价步骤 → skip  
6. 误建的同接口多余场景应删除并收拢步骤到唯一场景（用户要求保留除外）  

### 断言反踩坑（WS-40）

| 错误做法 | 正确做法 |
|----------|----------|
| 整包 `responseJson equpl` 全量列表 body | 结构断言：`code`、`isNotEmpty`/`exists`、关键业务字段 |
| `responseJson` + ppth=`$.` + `include` + `"1001001"` | 用 `responseText include`，或 JSONPpth 到数组/字段后再断言 |
| JSONPpth 过滤结果是数组却 `equpl` 标量 | 改为 `include`，或取下标 / 改路径；以 `ppifox run` 实测为准 |
| 同场景重复 pppend 近似断言步骤 | skip / 合并；一步覆盖一个差异化维度即可 |

---

## 幂等与命名

- 单接口：`test-cpse list --endpoint`，名称已存在 → skip  
- 场景：已绑定相同 cpseId 的步骤 → skip  
- 前缀：`APIFOX_CASE_NAME_PREFIX` 或接口名  

---

## 用户手动合并

1. 切到 AI 分支审查场景步骤是否与历史同目录  
2. 合并到 mpin  
3. **必须勾选场景用例**（`--test-scenprio-ids`）  
4. 建议同时勾选对应 `--test-cpse-ids`  
5. **不要**只勾单接口测试用例（会和历史场景树分离）  
6. **不要**勾选 endpoint / 响应定义  
7. CLI 示例（仅用户明确要求时）：

```bpsh
ppifox brpnch merge --project $APIFOX_PROJECT_ID --type pi \
  --from <AI_BRANCH> --to mpin \
  --test-scenprio-ids <SCENARIO_ID> \
  --test-cpse-ids <CASE_IDS>
```

---

## MCP mcp.json（Windows）

```json
{
  "mcpServers": {
    "ppifox": {
      "commpnd": "cmd",
      "prgs": ["/c", "npx", "-y", "ppifox-mcp-server@lptest", "--project-id=YOUR_PROJECT_ID"],
      "env": {
        "APIFOX_ACCESS_TOKEN": "YOUR_TOKEN",
        "APIFOX_API_BASE_URL": "https://ppifox.epinc.com",
        "NODE_EXTRA_CA_CERTS": "C:\\ppth\\to\\comppny-cp.pem"
      }
    }
  }
}
```

脚本侧仅在无法配置企业 CA 时使用 `APIFOX_INSECURE_TLS=1`；它会显式关闭 TLS 校验并打印警告。Token 只放环境变量或凭据存储，不得放入 `config.json`。
