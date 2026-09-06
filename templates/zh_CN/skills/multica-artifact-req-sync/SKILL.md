---
name: multica-artifact-req-sync
description: 产品经理产物提交规范：Confluence + JIRA Story 创建/更新、链接回写、可选钉钉。用于 @ProductManager PRD 落地与 Review 后二次提交。
metadata:
  orchestrates:
    - multica-platform-confluence
    - multica-platform-jira
  origin:
    - multica-artifact-req-sync
  credentials:
    priority:
      - JIRA_USERNAME / JIRA_PASSWORD
      - JIRA_USERNAME / JIRA_PASSWORD
version: 2.0.0
---

# PM Artifact Publish（产品经理产物提交规范 · 编排）

## Purpose

**PRD 专用编排** — 调用 platform skill 完成 Confluence / JIRA **创建与更新**，回传稳定链接。不重复实现 REST 脚本。

> 内容结构由 `multica-requirement-analysis` 负责；本 skill 只管「提交到哪里、如何更新」。

## Platform 协作

| Platform skill | 本 skill 用途 |
| --- | --- |
| `multica-platform-confluence` | 创建/更新 PRD 页面、拉取已有页面 |
| `multica-platform-jira` | 创建/更新 Story、描述追加、流转、钉钉 |

凭据：`JIRA_USERNAME / JIRA_PASSWORD`（见 frontmatter 与 platform skill）。

智能体指令见 [`references/agent-instructions.md`](references/agent-instructions.md)；创建/更新细则见 [`references/publish-workflow.md`](references/publish-workflow.md)。

## @ProductManager 标准流程

```text
1. multica-requirement-analysis  — 结构化 PRD + 修订记录
2. multica-artifact-req-sync — 本 skill：Confluence + JIRA + 可选钉钉
```

## Workflow A：首次提交（创建）

1. **Confluence** — 在 PRD 父页面下创建页面（HTML/Markdown 由 spec 产出）：

```bash
bash scripts/confluence.sh create-page \
  "<title>" "<parent_id>" "<html>" "<space>"
# ↑ multica-platform-confluence；路径由 MULTICA_SKILLS_ROOT 解析
```

2. **JIRA Story** — 描述含 Confluence 链接：

```bash
bash scripts/jira.sh create-story \
  --project <KEY> --summary "<title>" --description "..." ...
# ↑ multica-platform-jira
```

3. 可选钉钉：`multica-platform-jira` → `notify-story`

或编排脚本：

```bash
export MULTICA_SKILLS_ROOT="/path/to/templates/skills"
bash scripts/publish-prd.sh --project PROJ --summary "..." --html-file prd.html \
  -- --need-user <user> --background "..." ...
```

4. **回传 Leader**：Confluence URL、JIRA Key、创建时间、修订版本号。

## Workflow B：Review 后二次提交（更新）

> **禁止**为同一需求重复 `create-story`；Review 修订走更新链路。

1. **Confluence** — 对已有页面 **upsert/update**（保留 pageId；修订记录写入正文）
2. **JIRA** — 对已有 Story：
   - `append-description` 或 `update` 摘要/描述（含「修订 vN」与 Confluence 链接）
   - **禁止**新建第二个 Story 代替修订
3. 回传更新后的链接 + 修订版本号，供 ProductReviewer **复审**

## Workflow C–E

状态流转、排期、Confluence 阻塞降级（Workflow E：PRD 全文写入 JIRA 描述）——见 `multica-platform-jira` / `multica-platform-confluence` SKILL.md。

## 配置

- PRD 父页面 / space：`multica-platform-confluence/config.yaml`
- JIRA 字段 / 项目：`multica-platform-jira/config.yaml`
- 本目录 `config.yaml`：团队 PRD 默认值与钉钉映射（向后兼容）

## 用法（角色侧）

```text
先用 multica-requirement-analysis 结构化 PRD，
再用 multica-artifact-req-sync 落地并回传链接；
Review FAIL 后修订 PRD，再用 publish Workflow B 更新（勿重复创建 Story）。
```

## 为什么有效

JIRA / Confluence 共用 platform skill；**创建 vs 更新**分离，避免 Review 迭代产生重复 Story；编排通过 skill 名 + `MULTICA_SKILLS_ROOT` 定位。
