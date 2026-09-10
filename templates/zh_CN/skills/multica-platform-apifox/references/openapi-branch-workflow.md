# OpenAPI 同步 · AI 分支工作流

**适用**：`sync_openapi.js`（@BackendDev 经 `multica-artifact-backend` 调用）。  
**与场景补充区分**：接口**定义**同步每次新建分支；场景**用例**补充见 `reference.md` § AI 分支策略（可复用同 Issue 分支）。

---

## 强制规则

| 规则 | 说明 |
| --- | --- |
| **禁止直写 main** | OpenAPI 导入、打标、删 orphan 必须在 AI 分支执行 |
| **每次同步新建分支** | 同一 Issue 每次发布/变更 `openapi.json` 并同步 Apifox 时，**必须** `branch create` 新 AI 分支，不得复用上轮已 merge 的分支 |
| **分支命名** | `ai/<ISSUE-KEY>-openapi-<YYYYMMDD>`；同日多次同步递增 `-r2`、`-r3` |
| **合并** | 默认由人类在 Apifox 客户端 review 后 `branch merge`；Agent 不得自行 merge 到 main（除非 Leader 书面授权） |

---

## 标准步骤（每次 Backend 契约同步）

### 1. 解析项目

```bash
node scripts/systems-registry.js lookup --name "<系统名>"
# 或用户给出 APIFOX_PROJECT_ID
```

### 2. 创建 AI 分支

```bash
export APIFOX_PROJECT_ID=<id>
export APIFOX_ACCESS_TOKEN=<token>

# 分支名示例：ai/CDS2-1813-openapi-20260902
BRANCH="ai/<ISSUE-KEY>-openapi-$(date +%Y%m%d)"
apifox branch create --project $APIFOX_PROJECT_ID --name "$BRANCH" \
  --from main --type ai --api-base-url https://apifox.example.com
```

若同名已存在（同日重复同步），改用 `ai/<ISSUE-KEY>-openapi-<YYYYMMDD>-r2`。

### 3. 在分支上同步 OpenAPI

```bash
node scripts/sync_openapi.js \
  --file docs/backend/<ISSUE-KEY>/openapi.json \
  --issue <ISSUE-KEY> \
  --tag <ISSUE-KEY> \
  --branch "$BRANCH" \
  --json
```

### 4. 回传证据

写入 API 契约修订记录 / Leader 评论：

- AI 分支名
- `sync_openapi.js` JSON 摘要（imported / tagged / deleted）
- 未 merge 时注明「待人类 review 后 merge」

### 5. （可选）合并到 main

```bash
apifox branch merge --project $APIFOX_PROJECT_ID --type ai \
  --from "$BRANCH" --to main \
  --api-base-url https://apifox.example.com
```

merge 422001（main 未开 AI 写）→ 在 Apifox **客户端**合并，见 `reference.md`。

---

## Tester 并行场景补充

T1 写接口场景时：

1. 优先 **pick-to** 本 Issue 的 OpenAPI 分支（`ai/<ISSUE-KEY>-openapi-*`）上已同步的 endpoint  
2. 若 Backend 尚未同步，Tester 可在同命名规则下自建 `ai/<ISSUE-KEY>-scenarios-<YYYYMMDD>`，但 **不得** 在 main 上 create 用例  
3. OpenAPI 变更后 Backend 新建 openapi 分支 → Tester 在新分支上 `pick-to` 再补场景

---

## 环境变量

| 变量 | 用途 |
| --- | --- |
| `APIFOX_SOURCE_BRANCH` | 仅作 **create --from** 源分支，默认 `main`；**不是** sync 目标分支 |
| `--branch` / `APIFOX_BRANCH` | 本次 sync **目标** AI 分支（必填，禁止省略走 main） |

---

## 常见错误

| 现象 | 处理 |
| --- | --- |
| 省略 `--branch` 写到 main | 停止；create 新 AI 分支后重跑 sync |
| 复用已 merge 的旧分支做第二次 OpenAPI 变更 | 违规；必须 create 新分支 |
| create 后 list 看不到 endpoint | 确认 sync 与 create 使用同一 `--branch` |
