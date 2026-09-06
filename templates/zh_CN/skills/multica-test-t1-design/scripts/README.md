# multica-test-t1-design / scripts

> 本 skill 的 T1 落地脚本；内容规范见 `../references/`。采集走 platform skill（`fetch_all` 按 **skill 名** 定位 platform 脚本）。

## 随本 skill 发布的脚本

| 脚本 | 用途 |
| --- | --- |
| `fetch_all.py` | 一键采集 Issue + 团队文档（含图片）+ 设计稿（调 `multica-platform-jira` / `-confluence` / `-figma`） |
| `generate_xmind.py` | 功能用例 → 双格式 XMind（Zen JSON + XMind 8 XML） |
| `dedup_check.py` | 用例去重检查 |
| `generate_test_cases.py` | 结构化用例 dataclass 辅助 |
| `local_env.py` | 加载 `config.local.env` / 环境变量 |

## 团队自备（**不随本 skill 发布**）

批量把用例导入测试管理平台的脚本，强绑定具体工具（Jira 用例插件 / TestRail / Zephyr / 自研平台…），无法通用化。

- 约定名：`import_to_tracker.py`
- 接口与验收约定见 [`../references/import-contract.md`](../references/import-contract.md)
- **硬约束**：只有收到人类明确口令后才能运行；每批只导入一次

## Platform 单步调试（非 T1 日常入口）

| Platform skill | 脚本 |
| --- | --- |
| `multica-platform-jira` | `get_issue.py` / `jira_cli.py get-issue` |
| `multica-platform-confluence` | `fetch_page_by_url.py` |
| `multica-platform-figma` | `fetch_file.py` |

## 常用命令

```bash
# 采集
python scripts/fetch_all.py --jira-url https://your-domain.atlassian.net/browse/PROJ-123 -o ./data

# XMind（双格式）
python scripts/generate_xmind.py \
  --input ./data/test_cases.json \
  --output ./data/test_cases_PROJ-123.xmind \
  --project PROJ

# 导入（团队自备脚本；仅功能用例；口令后）
python scripts/import_to_tracker.py \
  --jira-url "https://your-domain.atlassian.net/browse/PROJ-123" \
  --input ./data/test_cases.json \
  --suite-name "<需求标题>"
```

## 编码与用例树注意

- **UTF-8**：JSON / XMind / 脚本 stdout 均按 UTF-8；Windows 终端乱码时先 `chcp 65001` 或设 `PYTHONIOENCODING=utf-8`
- **用例树**：XMind 与导入脚本都依赖 `module` 字段的 `/` 层级；层级写错会导致用例挂错节点
- **去重**：生成阶段按「模块 + 场景 + 操作路径」去重；导入阶段另有一次目标平台侧去重，两边都要做
