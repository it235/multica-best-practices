# multica-artifact-cicd-sync 使用说明

CICD 落地编排 skill：把代码评审结论转为 Jenkins 触发参数，调用 **`multica-platform-jenkins`** 跑构建 / 发布。

## 1. 前置依赖

- 已挂载 `multica-platform-jenkins`（提供 Jenkins URL 与凭据）。
- 本 Skill 的 `config.yaml` 中 `issue_service_map` 为占位示例，请按你的「Issue 前缀 → 触发服务」映射填写。

## 2. 配置

```bash
cp .env.example .env
# 通常无需额外变量；Jenkins 凭据由 multica-platform-jenkins/.env 提供
```

## 3. 安装依赖

```bash
cd scripts
pip install -r requirements.txt   # 仅 requests
```

## 4. 主要脚本

| 脚本 | 作用 | 示例 |
|---|---|---|
| `trigger_cicd.py` | 根据评审结论触发对应 service 的 CICD | `python scripts/trigger_cicd.py --issue <ISSUE_KEY> --env sit --service <service>` |
| `按 skill 名.py` | 解析依赖的 platform skill 路径 | `python scripts/按 skill 名.py` |
| `validate.py` | 校验入参 / 配置 | `python scripts/validate.py --issue <ISSUE_KEY>` |

## 5. 注意事项

- `config.yaml` 的 `issue_service_map` 前缀（`<ISSUE_PREFIX_A>` 等）为占位，请按你的团队习惯替换。
- 真实 Jenkins 地址 / job 名请放在 `multica-platform-jenkins` 中，本 Skill 不持有基建信息。
