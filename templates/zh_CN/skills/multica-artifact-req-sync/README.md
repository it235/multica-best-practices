# multica-artifact-req-sync

PRD 落地编排 skill：默认保存为仓库内 Markdown；明确需要时才调用 **`multica-platform-confluence`** + **`multica-platform-jira`**。

## 快速开始

1. 复制本目录到 Multica Skills。
2. 默认本地模式无需配置，直接运行：

```bash
bash scripts/publish-local.sh --issue-id <ISSUE-ID> --input <PRD.md>
```

脚本返回 `artifacts/<issue-id>/prd.md`，下游以此仓库相对路径定位。

3. 只有需要外部同步时，再复制两个 platform skill（或设置 `MULTICA_SKILLS_ROOT` 指向 `templates/skills/`）并配置凭据：

```bash
cp ../multica-platform-confluence/.env.example ../multica-platform-confluence/.env
cp ../multica-platform-jira/.env.example ../multica-platform-jira/.env
```

4. 外部团队落点：
- Confluence PRD 父页面：`multica-platform-confluence/config.yaml`
- JIRA 字段 / 项目：`multica-platform-jira/config.yaml`

## 编排脚本

```bash
export MULTICA_SKILLS_ROOT="/path/to/templates/skills"
bash scripts/publish-prd.sh --project <PROJECT_A> --summary "标题" --html-file prd.html \
  -- --need-user user --background "..."
```

## 文档

见 `SKILL.md`；Platform 命令详见 `multica-platform-confluence` 与 `multica-platform-jira` 的 SKILL.md（按 skill 名称挂载，勿写死路径）。
