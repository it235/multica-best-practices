# Jenkins CI/CD Reference（cicd 空间 · dev / sit）

> 完整 Job 清单：`jobs-catalog.yaml`（逻辑 `service` → `<jenkins-job-dev-pattern>` / `<jenkins-job-sit-pattern>` / `<jenkins-job-crm-dev-pattern>`）

## 环境

| 环境 | Job 命名 | 示例 |
| --- | --- | --- |
| dev | `<jenkins-job-dev-service>` / `<jenkins-job-crm-dev-service>` | `<jenkins-job-dev-example>` |
| sit | `<jenkins-job-sit-service>` | `<jenkins-job-sit-example>` |

Base URL：`http://<JENKINS_URL>`

## 常用命令

```bash
# 列出 sit 全部可触发 service
python scripts/list_jobs.py --env sit

# 查单个 service 对应 Job 名
python scripts/list_jobs.py --env dev --service <service>

# 触发 dev / sit（deploy branch，非 feature）
python scripts/trigger_env.py --env dev --service <service> --branch release/<ISSUE_KEY>-xxx

python scripts/trigger_env.py --env sit --service <service1>,<service2> --branch release/<ISSUE_KEY>-xxx --json
```

## 编排（Multica DevOps）

```bash
python ../multica-artifact-cicd-sync/scripts/trigger_cicd.py \
  --issue <ISSUE_KEY> --env dev --service <service> --branch release/<ISSUE_KEY>-xxx --json
```

`issue_service_map` 已配置 `<ISSUE_PREFIX_A>` / `<ISSUE_PREFIX_B>` / `<ISSUE_PREFIX_C>` / `<ISSUE_PREFIX_D>` 前缀，可只传 `--issue` 不传 `--service`。

## 命名不一致（已写入 catalog）

| service | dev | sit |
| --- | --- | --- |
| apisix-v3 | <jenkins-job-dev-example-1> | <jenkins-job-sit-example-1> |
| <service-gw-jurisdiction> | <jenkins-job-dev-example>_gw_jurisdiction_service | <jenkins-job-sit-example-2> |
| pmm-report-generator | <jenkins-job-dev-example-3> | <jenkins-job-sit-example-3> |
| modelService | <jenkins-job-dev-example-4> | <jenkins-job-sit-example-4> |

## 构建 displayName 模式（参考）

- dev：`{build}_{module}_{branch}_dev_{version}`
- sit：`{build}_{module}_{branch}_sit_{version}` 或 `deployVersion_sit_{version}`

## 参数

**默认**：从该 Job 最近一次 **SUCCESS** 构建复制全部参数，**仅**用 `--branch` 覆盖分支类参数（branchName / branch / gitBranch …）。`--param` 可覆盖任意项；`--no-last-success` 关闭种子行为。

```bash
# 发现（查看 last_success + resolved）
python scripts/trigger_env.py --env sit --service <service> --branch feature/foo --discover-only --json

# 触发（deployVersion / env 等沿用上次 SUCCESS）
python scripts/trigger_env.py --env sit --service <service> --branch feature/foo --json

# 手动覆盖单个参数
python scripts/trigger_env.py --env sit --service <service> --branch feature/foo --param deployVersion=1.75.0_795 --json
```

## 跨平台

Python 3，Windows / Linux 命令一致。JIRA 回写仍需要 bash。






