# multica-platform-jira 使用说明

JIRA 平台外壳：读写 issue、评论、状态流转、DingTalk 通知。所有 URL 与凭据均为占位，使用方在 `.env` 填入自己的 JIRA 地址。

## 1. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env，填入：
#   JIRA_URL=http://your-jira.example.com:8080
#   JIRA_USER=<your-user>
#   JIRA_PASS=<your-pass>
#   ATLASSIAN_USER=<your-domain-user>      # 可选，域账号优先
#   ATLASSIAN_PASS=<your-domain-pass>
#   DINGTALK_WEBHOOK=<webhook-token>       # 可选，通知用
```

凭据读取优先级：`ATLASSIAN_USER/PASS` → `JIRA_USER/PASS` → `.env`。

## 2. 主要入口

主脚本为 `scripts/jira.sh`（bash），支持子命令。常用：

```bash
bash scripts/jira.sh --help
bash scripts/jira.sh issue <ISSUE_KEY>              # 查看 issue 详情
bash scripts/jira.sh comment <ISSUE_KEY> "结论..."  # 添加评论
bash scripts/jira.sh transition <ISSUE_KEY> "审核通过"  # 状态流转
bash scripts/jira.sh list --project <PROJECT_KEY> --status 待审核  # 按条件列出
```

字段 ID（如 `<JIRA_CUSTOM_FIELD_XXX>`）在 `config.yaml` 中以占位形式给出，请按你的 JIRA 实例替换为真实 customId。

## 3. 校验

```bash
bash scripts/validate.sh   # 检查 credentials / 必填字段
```

## 4. 注意事项

- `config.yaml` 中的 `customId`、`pageId`、项目 `id` 均为占位，**请按你的 JIRA 实例填写**。
- 不要在 `.env` 或 `config.yaml` 提交真实 token / 密码。
