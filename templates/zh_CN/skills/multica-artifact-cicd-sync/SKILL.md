---
name: multica-artifact-cicd-sync
description: CI/CD 产物编排：G2 PASS 且代码已 push 后调用 multica-platform-jenkins 触发 dev/sit 构建，回写 JIRA 并回传部署 URL。Python 实现，Windows / Linux 通用。
metadata:
  orchestrates:
    - multica-platform-jenkins
    - multica-platform-jira
  runtime:
    python: ">=3.10"
---

# Artifact · CI/CD Sync（编排）

## Purpose

G2 PASS + push 后，调用 `multica-platform-jenkins` 触发 dev/sit Job。**参数由 Jenkins API 自动发现**，编排层不硬编码参数名。

## Platform 协作

| Platform skill | 本 skill 用途 |
| --- | --- |
| `multica-platform-jenkins` | `trigger_env.py` / `trigger_cicd.py` 触发与轮询 |
| `multica-platform-jira` | 可选读 Issue；回写部署链接 |

凭据：`JIRA_USERNAME / JIRA_PASSWORD`（与 JIRA 共用域账户）。CLI 细节见 platform-jenkins SKILL。

## Agent 流程

```text
1. discover-only（推荐先跑，检查 missing）：
   python scripts/trigger_cicd.py --issue PROJ-1853 --env sit --branch release/PROJ-1853-聚合页 --discover-only --json
2. 触发（**只用 Issue deploy branch，不用 feature 分支**）：
   python scripts/trigger_cicd.py --issue PROJ-1853 --env sit --branch release/PROJ-1853-聚合页 --json
3. missing 参数：追加 --param name=value（trigger_cicd 需扩展传参时走 trigger_env --param）
```

## 参数解析策略

默认（`use_last_success=true`）：

1. 读取 `lastSuccessfulBuild` 的全部构建参数
2. **仅**将分支类参数（branchName / branch / gitBranch …）替换为 `--branch`
3. `--param` 可覆盖任意项；`--no-last-success` 关闭此行为

---

## Workflow A：dev 部署

```bash
python scripts/trigger_cicd.py \
  --issue PROJ-1853 \
  --env dev \
  --service acme \
  --branch release/PROJ-1853-聚合页 \
  --json
```

## Workflow B：sit 部署（G2.5 → Tester T3）

```bash
python scripts/trigger_cicd.py \
  --issue PROJ-1853 \
  --env sit \
  --branch release/PROJ-1853-聚合页 \
  --json
```

`acme` / `MSD` / `ERP` / `IAM` 等前缀已在 `config.yaml` → `issue_service_map` 配置，可省略 `--service`。

## Workflow C：多服务

```bash
python scripts/trigger_cicd.py --env sit --service mes2,mes-ui-v2 --branch release/MSD-26092-xxx --json
```

## 用法（角色侧）

```text
G2 PASS 且代码已 push 后，用 multica-artifact-cicd-sync 触发 Jenkins 并回传部署链接。
```

## 为什么有效

编排层只依赖 Python；Issue 前缀自动映射到 `jobs-catalog.yaml` 中的 logical service。
