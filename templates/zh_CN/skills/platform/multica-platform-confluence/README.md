# multica-platform-confluence 使用说明

Confluence 平台外壳：发布设计文档 / PRD 到指定空间页面。所有 URL 与凭据均为占位，使用方在 `.env` 填入自己的 Confluence 地址。

## 1. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env，填入：
#   CONFLUENCE_URL=http://your-confluence.example.com:8090
#   CONFLUENCE_USER=<your-user>
#   CONFLUENCE_PASS=<your-pass>
#   CONFLUENCE_AUTH_MODE=basic
#   ATLASSIAN_USER=<your-domain-user>      # 可选，域账号优先
#   ATLASSIAN_PASS=<your-domain-pass>
```

空间清单在 `spaces.json`（已脱敏为占位骨架），按你的 Confluence 实例填写 `key` / `name`。

## 2. 安装依赖

```bash
cd scripts
pip install -r requirements.txt
```

## 3. 主要脚本

| 脚本 | 作用 | 示例 |
|---|---|---|
| `publish_design.py` | 把 Markdown 设计文档发布为 Confluence 页面 | `python scripts/publish_design.py <ISSUE_KEY>` |
| `fetch_page.py` | 拉取页面转 Markdown（便于二次编辑） | `python scripts/fetch_page.py <CONFLUENCE_PAGE_ID> -o out.md` |
| `confluence.sh` | bash 封装（创建 / 更新 / 附件） | `bash scripts/confluence.sh --help` |

页面模板在 `scripts/templates/`（`design-template.md` / `prd-template.md`）。

## 4. 校验

```bash
bash scripts/validate.sh   # 检查 credentials / 空间配置
```

## 5. 注意事项

- `config.yaml` 里的 `<CONFLUENCE_PARENT_PAGE_ID>`、空间 `key` 为占位，请按你的实例填写。
- 不要提交真实页面 ID / 空间 key / token。
