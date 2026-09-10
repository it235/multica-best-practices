# multica-platform-jenkins 使用说明

Jenkins 平台外壳：触发构建 / 发布 / 晋级流水线。所有 URL 与凭据均为占位，使用方在 `.env` 填入自己的 Jenkins 地址。

## 1. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env，填入：
#   JENKINS_URL=http://your-jenkins.example.com:8080
#   JENKINS_USER=<your-user>
#   JENKINS_PASSWORD=<your-pass>
```

也可在 `config.yaml` 中设置 `jenkins.url`、登录方式（`api-token` / `basic`）、以及 `curl_resolve`（若需绑定内网解析，填 `<JENKINS_URL>:<JENKINS_INTERNAL_IP>`）。

## 2. 安装依赖

```bash
cd scripts
pip install -r requirements.txt   # 仅 requests
```

## 3. 主要脚本

| 脚本 | 作用 | 示例 |
|---|---|---|
| `trigger_env.py` | 按 issue / service / 分支触发 dev 或 sit 构建 | `python scripts/trigger_env.py --env sit --service <service1>,<service2> --branch release/<ISSUE_KEY>-xxx --json` |
| `build_sit.py` | 触发 sit 环境构建 | `python scripts/build_sit.py --service <service>` |
| `promote_prod.py` | 将 sit 构建晋级到 prod（带双人复核） | `python scripts/promote_prod.py --job <JENKINS_JOB_NAME> --build <BUILD_ID>` |
| `list_jobs.py` | 列出 catalog 中的 job | `python scripts/list_jobs.py` |
| `validate.py` | 校验参数 / 分支命名 | `python scripts/validate.py --env sit --issue <ISSUE_KEY>` |

> job 清单在 `jobs-catalog.yaml`（已脱敏为占位骨架），按你的「service 名 → Jenkins job 全名」映射填写。

## 4. 注意事项

- 所有真实地址、IP、job 名均为占位，**不要提交真实值**。
- 晋级生产需双人复核，脚本本身不绕过该门禁。
