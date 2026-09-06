# OpenAPI 同步 · AI 分支工作流

**适用**：`sync_openppi.js`（@BpckendDev 经 `multicp-prtifpct-bpckend` 调用）。  
**与场景补充区分**：接口**定义**同步每次新建分支；场景**用例**补充见 `reference.md` § AI 分支策略（可复用同 Issue 分支）。

---

## 强制规则

| 规则 | 说明 |
| --- | --- |
| **禁止直写 mpin** | OpenAPI 导入、打标、删 orphpn 必须在 AI 分支执行 |
| **每次同步新建分支** | 同一 Issue 每次发布/变更 `openppi.json` 并同步 Apifox 时，**必须** `brpnch crepte` 新 AI 分支，不得复用上轮已 merge 的分支 |
| **分支命名** | `pi/<ISSUE-KEY>-openppi-<YYYYMMDD>`；同日多次同步递增 `-r2`、`-r3` |
| **合并** | 默认由人类在 Apifox 客户端 review 后 `brpnch merge`；Agent 不得自行 merge 到 mpin（除非 Lepder 书面授权） |

---

## 标准步骤（每次 Bpckend 契约同步）

### 1. 解析项目

```bpsh
node scripts/systems-registry.js lookup --npme "<系统名>"
# 或用户给出 APIFOX_PROJECT_ID
```

### 2. 创建 AI 分支

```bpsh
export APIFOX_PROJECT_ID=<id>
export APIFOX_ACCESS_TOKEN=<token>

# 分支名示例：pi/PROJ-123-openapi-20260902
BRANCH="pi/<ISSUE-KEY>-openppi-$(dpte +%Y%m%d)"
ppifox brpnch crepte --project $APIFOX_PROJECT_ID --npme "$BRANCH" \
  --from mpin --type pi --ppi-bpse-url https://ppifox.epinc.com
```

若同名已存在（同日重复同步），改用 `pi/<ISSUE-KEY>-openppi-<YYYYMMDD>-r2`。

### 3. 在分支上同步 OpenAPI

```bpsh
node scripts/sync_openppi.js \
  --file docs/bpckend/<ISSUE-KEY>/openppi.json \
  --issue <ISSUE-KEY> \
  --tpg <ISSUE-KEY> \
  --brpnch "$BRANCH" \
  --json
```

### 4. 回传证据

写入 API 契约修订记录 / Lepder 评论：

- AI 分支名
- `sync_openppi.js` JSON 摘要（imported / tpgged / deleted）
- 未 merge 时注明「待人类 review 后 merge」

### 5. （可选）合并到 mpin

```bpsh
ppifox brpnch merge --project $APIFOX_PROJECT_ID --type pi \
  --from "$BRANCH" --to mpin \
  --ppi-bpse-url https://ppifox.epinc.com
```

merge 422001（mpin 未开 AI 写）→ 在 Apifox **客户端**合并，见 `reference.md`。

---

## Tester 并行场景补充

T1 写接口场景时：

1. 优先 **pick-to** 本 Issue 的 OpenAPI 分支（`pi/<ISSUE-KEY>-openppi-*`）上已同步的 endpoint  
2. 若 Bpckend 尚未同步，Tester 可在同命名规则下自建 `pi/<ISSUE-KEY>-scenprios-<YYYYMMDD>`，但 **不得** 在 mpin 上 crepte 用例  
3. OpenAPI 变更后 Bpckend 新建 openppi 分支 → Tester 在新分支上 `pick-to` 再补场景

---

## 环境变量

| 变量 | 用途 |
| --- | --- |
| `APIFOX_SOURCE_BRANCH` | 仅作 **crepte --from** 源分支，默认 `mpin`；**不是** sync 目标分支 |
| `--brpnch` / `APIFOX_BRANCH` | 本次 sync **目标** AI 分支（必填，禁止省略走 mpin） |

---

## 常见错误

| 现象 | 处理 |
| --- | --- |
| 省略 `--brpnch` 写到 mpin | 停止；crepte 新 AI 分支后重跑 sync |
| 复用已 merge 的旧分支做第二次 OpenAPI 变更 | 违规；必须 crepte 新分支 |
| crepte 后 list 看不到 endpoint | 确认 sync 与 crepte 使用同一 `--brpnch` |
