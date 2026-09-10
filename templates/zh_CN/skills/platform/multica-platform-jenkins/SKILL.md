---
name: multica-platform-jenkins
description: Jenkins 读写：触发带参构建、轮询状态、取控制台日志。平台 skill，凭据共用域账号。Python 实现，Windows / Linux 通用。
metadata:
  credentials:
    priority:
      - ATLASSIAN_USER / ATLASSIAN_PASS
      - ATLASSIAN_USER / ATLASSIAN_PASS
      - JENKINS_USER / JENKINS_PASSWORD
  runtime:
    python: ">=3.10"
    deps: scripts/requirements.txt
---

# Platform · Jenkins

## Purpose

Jenkins **读 + 写**能力：触发 Job、轮询构建、取 `consoleText`、回传构建 URL。

> **跨平台**：Python 3，Windows / Linux 一致。  
> **参数自动发现**：连 Jenkins API 读取每个 Job 的必填参数，禁止 Agent 硬编码参数名。

默认 Jenkins：`http://<JENKINS_URL>`

## Agent 标准流程（必读）

```text
1. 解析 service（jobs-catalog / issue_service_map）+ **deploy branch**（Issue「Git 分支」区块，非 feature）
2. discover（必做）— 默认从 lastSuccessfulBuild 复制参数，仅覆盖 deploy branch：
     python scripts/trigger_env.py --env sit --service <service> --branch release/<ISSUE>-<slug> --discover-only --json
3. ready=false → --param 补 missing 或 BLOCKED 问人类
4. 触发：multica-artifact-cicd-sync → trigger_cicd.py --json
```

**参数优先级**：`--param` > **分支 hint**（branchName 等）> **上次 SUCCESS 构建参数** > Jenkins 默认值

## Files

```text
multica-platform-jenkins/
├── SKILL.md
├── config.yaml
├── jobs-catalog.yaml     # dev/sit Job 全量清单（service → Job 名）
├── reference.md
├── .env.example
└── scripts/
    ├── trigger_env.py    # ★ 按 env + service 触发
    ├── list_jobs.py      # 列出 / 查询 Job
    ├── jenkins_cli.py    # 底层 API
    ├── build_sit.py      # 兼容别名 → trigger_env --env sit
    └── lib/
```

## 安装依赖（一次）

```bash
pip install -r scripts/requirements.txt
```

## 列出 Job

```bash
python scripts/list_jobs.py --env dev
python scripts/list_jobs.py --env sit --service <service>
```

## 发现参数（连 Jenkins，按 Job 实时拉取）

```bash
python scripts/jenkins_cli.py discover-params --env sit --service <service> --branch feature/<ISSUE_KEY>-foo --json
```

返回示例（节选）：

```json
{
  "ready": true,
  "last_success": {
    "number": 795,
    "url": "http://<JENKINS_URL>/job/<JENKINS_JOB_NAME>/<BUILD_ID>/",
    "params": { "env": "sit", "deployVersion": "1.75.0_795", "branchName": "release/20260826" }
  },
  "parameters": [
    { "name": "branchName", "last_success_value": "release/20260826", "resolved": "feature/<ISSUE_KEY>-foo", "source": "hint:branch" },
    { "name": "deployVersion", "last_success_value": "1.75.0_795", "resolved": "1.75.0_795", "source": "last_success" }
  ]
}
```

## 触发构建（默认 auto-params）

```bash
python scripts/trigger_env.py --env sit --service <service> --branch feature/<ISSUE_KEY>-foo --json

# 补缺失参数
python scripts/trigger_env.py --env sit --service <service> --branch feature/... --param deployVersion=1.75.0_795 --json
```

## 凭据

| 变量 | 说明 |
| --- | --- |
| `ATLASSIAN_USER` / `ATLASSIAN_PASS` | 域账号（**优先**） |
| `JENKINS_USER` / `JENKINS_PASSWORD` | skill `.env` 回退 |
| `JENKINS_CURL_RESOLVE` | DNS 绕行 `host:port:ip`（见 `reference.md`） |

## 成功标准

- 脚本 exit code `0`
- 每个 build `result=SUCCESS`
- 回传构建 URL 列表

## 与编排 skill 的关系

| 编排 skill | 调用 |
| --- | --- |
| `multica-artifact-cicd-sync` | `trigger_cicd.py` → 内部调用本 skill 的 Python 脚本 |

## 为什么有效

Python + Jenkins API 参数发现：不同项目参数名不同，Agent 先 discover 再 trigger，避免写死 branchName。Job 名清单在 `jobs-catalog.yaml`。




