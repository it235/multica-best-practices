# MULTICA — 本仓库 Squad 上下文

> **复制到产品仓库根目录**（前后端分仓时 **各仓一份**）。
> @Tester / @FrontendDev / @BackendDev / Leader 开工前 **必读**；路径以本文件为准，**禁止猜测**。

---

## 1. 仓库身份

| 字段 | 填写 |
| --- | --- |
| **layout** | `monorepo`（前后端同仓）\| `frontend` \| `backend` \| `fullstack` \| `other` |
| **服务名**（CI `--service`） | <!-- 如 acme-web；纯库 / 无部署填 N/A --> |
| **关联仓库**（分仓时） | <!-- frontend: acme-frontend → backend: acme-api --> |

---

## 2. 测试自动化路径（Tester 写脚本 / T3 执行前必读）

### 2.1 本仓路径（只填本 repo 实际存在的）

| 类型 | 路径 | 说明 |
| --- | --- | --- |
| **UI E2E（Playwright）** | `tests/e2e/` | pytest + playwright；1 CASE = 1 `test_*.py` |
| **API manifest** | `tests/api/` | 每 Issue 子目录 `tests/api/<ISSUE-KEY>/manifest.json` |
| **单元测试** | <!-- 如 `npm test` / `pytest tests/unit` --> | Backend / Frontend 自测；G2 必绿 |
| **本地用例草稿**（可选） | `docs/test/<ISSUE-KEY>/` | 发布到团队平台前的草稿；非必须 |

**同仓（monorepo / fullstack）**：上表须 **完整** 填写 UI + API + 单测命令，Tester 只读本文件即可。

**分仓**：

- **前端仓** MULTICA.md：填 `tests/e2e/`（有则填路径）；API manifest 若无则写 `N/A（见 backend 仓 MULTICA.md）`
- **后端仓** MULTICA.md：填 `tests/api/`、单元测试命令；UI E2E 若无则写 `N/A（见 frontend 仓 MULTICA.md）`
- Issue **仓库矩阵** 须列出各仓 repo 名；Tester **按矩阵逐个读** 对应 MULTICA.md

### 2.2 API 测试平台（可选）

Git 里**不存步骤，只存索引**。

| 字段 | 值 |
| --- | --- |
| 默认 projectId | <!-- 或写「见团队 registry」 --> |
| manifest 路径 | 见上表 `tests/api/` |

场景步骤在 API 平台的分支上；manifest 记录 branch / scenarioIds。

---

## 3. 构建与验证命令（Leader G2 / CI 可选）

```text
install:   <!-- pnpm install / pip install -r ... -->
lint:      <!-- 可选 -->
unit_test: <!-- 必填；G2 证据 -->
build:     <!-- 可选 -->
e2e:       <!-- cd tests/e2e && pytest . -->
```

仓库已配 CI 时，Leader G2 **引用 CI 结论**，不重复跑（见 `multica-verification`）。

---

## 4. 分支约定（与 Issue deploy branch 对齐）

| 类型 | 命名 |
| --- | --- |
| deploy branch | `release/<ISSUE-KEY>-<slug>`（与 Issue 一致） |
| feature branch | `feature/<ISSUE-KEY>-<端>-<slug>` |

自动化脚本随 feature 合并到 **deploy branch** 之后再跑 T3。

---

## 5. 凭据（禁止写入 Git）

| 用途 | 环境变量名 |
| --- | --- |
| UI 登录 | <!-- 如 APP_UI_USERNAME / APP_UI_PASSWORD --> |
| API 测试平台 | `API_TEST_TOKEN`（Agent Secret） |

`.env` 已 gitignore；MULTICA.md **只写变量名**，不写值。

---

## 为什么要有这个文件

- 自动化路径因项目而异；**Issue 矩阵只说 repo 名，路径以 MULTICA.md 为准**。
- 分仓时各读各仓，避免 Tester 把 e2e 写进后端仓、或把 manifest 放错位置。
- 缺这个文件 = **BLOCKED**，请人工补齐后再写自动化。
