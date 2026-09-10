# Multica 模板同步 / Multica template sync

可选自动化：把本仓库 `templates/zh_CN` 下的 **skills / agents / squad** 推送到你的 Multica workspace。
Python 3.9+，**仅标准库**，全部操作**幂等**。
Optional automation that pushes this repo's templates to your Multica workspace — Python 3.9+, stdlib only, fully idempotent.

> 只想手动复制粘贴？直接用 [`templates/zh_CN/squad/software-development`](../../templates/zh_CN/squad/software-development) 即可，不必用脚本。
> Prefer copy-paste? Skip this folder — the starters work on their own.

## 一键建队（推荐入口）/ One-shot bootstrap

`bootstrap_squad.py` 按依赖顺序跑完 5 步，以**名称**为对齐键（已存在则更新、缺失才创建），
因此不必把任何 UUID 提交进仓库：

1. **skills** — `templates/zh_CN/skills/**/SKILL.md` → `POST /api/skills` / `PUT /api/skills/{id}`
2. **agents** — `templates/zh_CN/agents/<stem>.md` → `POST /api/agents`（需 `runtime_id`，自动探测）/ `PUT /api/agents/{id}`
3. **squad** — `POST /api/squads`（`leader_id` 必填）+ `PUT` 写入小队 instructions
4. **members** — `POST /api/squads/{id}/members`（`member_type=agent` + `role`）
5. **bindings** — `POST /api/agents/{id}/skills/add`（ensure，追加）或 `PUT /api/agents/{id}/skills`（replace，精确覆盖）

最快只需两条命令 —— 不传 `--config` 时会自动使用内置的 `squad-bootstrap.example.json`（15 个角色 + 各自挂载的 skills）：

```powershell
cd scripts/multica-sync

$env:MULTICA_API_TOKEN = "mul_xxx"                           # 推荐；Cookie 方式见下
$env:MULTICA_API_URL   = "https://your-multica.example.com"  # 或写进 config.local.json

python bootstrap_squad.py --workspace 100 --dry-run   # 先预览
python bootstrap_squad.py --workspace 100             # 再执行
```

想改角色或挂载时，复制一份配置再改：

```powershell
cp squad-bootstrap.example.json squad-bootstrap.json
python bootstrap_squad.py --workspace 100 --config squad-bootstrap.json
```

常用变体 / variants：

```powershell
python bootstrap_squad.py --workspace 100 --config squad-bootstrap.json --sync-skills all
python bootstrap_squad.py --workspace 100 --config squad-bootstrap.json --bind-mode replace
python bootstrap_squad.py --workspace 100 --config squad-bootstrap.json --only tester
python bootstrap_squad.py --workspace 100 --config squad-bootstrap.json --write-mapping agent-mapping.json
```

| 常用参数 | 说明 |
| --- | --- |
| `--workspace` | workspace slug 或 UUID（也可用 `MULTICA_WORKSPACE`） |
| `--config` | 引导配置，默认 `squad-bootstrap.json` |
| `--sync-skills` | `needed`（默认，仅配置引用到的）/ `all`（全部模板 skill）/ `none` |
| `--bind-mode` | `ensure`（默认，追加缺失绑定）/ `replace`（精确覆盖为该列表） |
| `--runtime` | 创建 agent 用的 runtime_id；不填则自动探测 |
| `--dry-run` | 只打印将要执行的操作，不写入 |

> 创建 agent 必须带 runtime：脚本默认取 `GET /api/runtimes?owner=me` 的第一个可用 runtime；
> 若 workspace 中无可见 runtime，用 `--runtime <runtime-id>` 显式指定。
> Creating an agent requires a runtime — pass `--runtime` when none is visible.

## 认证 / Authentication

**方式 A — API Token（推荐）**

```powershell
$env:MULTICA_API_TOKEN = "mul_xxx"
```

**方式 B — 浏览器 Cookie**（DevTools → 任意 Multica 请求的 Headers 复制）

```powershell
$env:MULTICA_COOKIE = "multica_auth=...; multica_logged_in=1; ..."
$env:MULTICA_CSRF   = "<x-csrf-token 或 multica_csrf cookie 的值>"
```

**地址 / Base URL** — 脚本内**不内置任何地址**，解析顺序：`--url` > `MULTICA_API_URL` > `config.local.json`

```powershell
$env:MULTICA_API_URL = "https://multica.example.com"
# 或在 config.local.json 中：{ "base_url": "https://multica.example.com", "workspace": "100" }
```

⚠️ 勿将 token / cookie / 内网地址提交 Git。`config.local.json`、`squad-bootstrap.json`、`agent-mapping.json` 已在 `.gitignore` 中。

## 跨 workspace 复制小队 / Clone a squad across workspaces

已有小队在某 workspace，想原样复制到另一个 workspace（agent / skill 不存在则创建，存在则复用并绑定）：

```powershell
cd scripts/multica-sync

# 预览
python clone_squad.py `
  --from-workspace 100 `
  --from-squad <source-squad-uuid> `
  --to-workspace 200 `
  --dry-run

# 执行
python clone_squad.py `
  --from-workspace 100 `
  --from-squad <source-squad-uuid> `
  --to-workspace 200

# 目标 workspace 无 runtime 时
python clone_squad.py ... --to-workspace 200 --runtime <runtime-id>

# 强制覆盖目标已有同名 skill / agent / squad 内容
python clone_squad.py ... --update-skills --update-agents --update-squad
```

| 参数 | 说明 |
| --- | --- |
| `--from-workspace` / `--from-squad` | 源 workspace slug/UUID + 源小队 UUID（小队页 URL 里 `/squads/<uuid>`） |
| `--to-workspace` | 目标 workspace slug/UUID |
| `--to-squad-name` | 目标小队名（默认与源同名） |
| `--runtime` | 目标新建 agent 用的 runtime_id；默认自动探测 |
| `--update-skills` / `--update-agents` / `--update-squad` | 同名已存在时覆盖内容（默认只复用不覆盖） |

> 复制按**名称**对齐（与 bootstrap 一致），因此重跑幂等；`--dry-run` 可先预览。
> Base URL 通过 `--url` / `MULTICA_API_URL` / `config.local.json` 提供，脚本不内置任何地址。

## 脚本说明 / Scripts

| 脚本 | 作用 |
| --- | --- |
| `bootstrap_squad.py` | **一键建队**：skills → agents → squad → members → bindings（幂等，按名称对齐） |
| `clone_squad.py` | **跨 workspace 复制小队**：从源 API 拉取 agents/skills/bindings，在目标 workspace 创建/复用/绑定（幂等，按名称对齐） |
| `sync_skills.py` | `templates/zh_CN/skills/**/SKILL.md` → workspace 创建 / 覆盖 |
| `sync_agents.py` | `templates/zh_CN/agents/*.md` → `PUT /api/agents/{id}`；`--squad` 按 role 自动映射 |
| `list_squad_skills.py` | 列出小队 agent 及其已绑定 skills |
| `squad_mapping.py` | role → 模板 stem 的映射（被 `sync_agents.py` 使用） |
| `multica_client.py` | 极简 REST 客户端（仅标准库） |
| `repo_paths.py` | 模板路径解析（`templates/zh_CN` 优先，兼容平铺布局） |

## 路径与多语言 / Paths & i18n

默认读 `templates/zh_CN`，可切换：

```powershell
$env:MULTICA_TEMPLATE_LANG = "en_US"            # 读 templates/en_US
$env:MULTICA_TEMPLATES_DIR = "templates/zh_CN"  # 或显式指定
```

配置里的 `instructions_file` 支持三种写法：绝对路径、`templates/...`、或相对模板根
（如 `squad/software-development/squad.md`）。
