---
name: multica-platform-confluence
description: Confluence 读写：页面拉取、PRD HTML 创建、Markdown 设计发布。平台 skill，与 JIRA 解耦；由产物编排 skill 调用。跨平台优先 Python CLI。
metadata:
  credentials:
    priority:
      - JIRA_USERNAME / JIRA_PASSWORD
      - JIRA_USERNAME / JIRA_PASSWORD
      - CONFLUENCE_USER / CONFLUENCE_PASS
  landing:
    prd_parent_page_id: config confluence.default_parent_page_id
    artifact_parent_from_jira: "JIRA 描述中 Confluence 需求页（Issue Hub）"
    artifact_parent_fallback: config confluence.design_parent_page_id
    design_local_draft: docs/design/<ISSUE-KEY>/design.md
---

# Platform · Confluence

## Platform 协作

本 skill 为 **platform 层**；供 artifact / T1 fetch 等按名调用。读：`fetch_page.py`、`fetch_page_by_url.py`；写：`publish_design.py`、PRD HTML。

## Purpose

Confluence **读 + 写**能力：拉取已有页面供 Agent 消费，把 PRD / 设计等产物落地并回传**稳定页面链接**。与 `multica-platform-jira` 解耦。

> **跨平台**：优先 `python scripts/*.py`（Windows / macOS / Linux）；`confluence.sh` 为 Unix 便利封装，非必需。

## Issue Hub 父页面模型

Issue 创建时已绑定 **JIRA 编号**；JIRA 描述里的 **Confluence 需求页** 是该需求的文档根（PRD Hub）。

| 产物 | 父页面 | 说明 |
| --- | --- | --- |
| PRD / 需求正文 | 团队默认目录或已有需求页 | PM 落地时创建或更新 |
| 技术设计等后续文档 | **JIRA 解析到的 Confluence 需求页** | 作为子页面 upsert |
| 回退 | `config.yaml` → `design_parent_page_id` | JIRA 无 Confluence 链接时 |

解析父 pageId：`multica-platform-jira` → `jira_cli.py get-confluence-url` / `resolve-parent-page-id`。

## Files

```text
multica-platform-confluence/
├── SKILL.md
├── config.yaml
├── spaces.json
├── .env.example
└── scripts/
    ├── confluence.sh          # Unix 便利封装（可选）
    ├── fetch_page.py          # Confluence pageId → local Markdown
    ├── fetch_page_by_url.py   # URL → Markdown + rich JSON + images（Tester fetch_all）
    ├── publish_design.py      # Markdown 设计 upsert（推荐，跨平台）
    ├── lib/md_to_confluence.py
    ├── lib/html_to_md.py
    ├── requirements.txt
    └── templates/
        ├── prd-template.md
        ├── design-template.md
        ├── backend-api-template.md
        └── frontend-impl-template.md
```

## Read

```bash
pip install -r scripts/requirements.txt
python scripts/fetch_page.py <page_id> [output_dir] [jira_key]

# 按 URL 拉取（含图片、子页面）— Tester fetch_all 使用
python scripts/fetch_page_by_url.py --url "<confluence-url>" \
  --output out.md --json out.json --image-dir ./images
```

Unix 可选：`bash scripts/confluence.sh fetch-page <page_id> ...`

**典型链路**：JIRA Issue → `multica-platform-jira` `get-confluence-url` → 本 skill `fetch_page.py` 拉 PRD / 设计正文。

## Write · 技术设计（Markdown → Confluence）

1. @Architect 写本地 `docs/design/<ISSUE-KEY>/design.md`（基线见 `scripts/templates/design-template.md`）。
2. 发布（**默认父页面 = JIRA 需求 Confluence 页**，并回写 JIRA）：

```bash
pip install -r scripts/requirements.txt
python scripts/publish_design.py <ISSUE-KEY> docs/design/<ISSUE-KEY>/design.md \
  --append-jira --json
```

| 参数 | 作用 |
| --- | --- |
| `--append-jira` | 发布后调用 `multica-platform-jira` 追加设计链接到 Issue 描述 |
| `--parent <pageId>` | 显式指定父页面（覆盖 JIRA 解析） |
| `--no-parent-from-jira` | 不从 JIRA 解析；仅用 config 回退父页面 |
| `--space` / `--title` | 覆盖 space / 标题 |

**Upsert 规则**：同 space + 同 title 则更新版本；title 自动加 `[AI]` 后缀。

## Write · PRD 页面（HTML）

Unix：`bash scripts/confluence.sh create-page ...`  
或由 `multica-artifact-req-sync` 编排调用。

## 与产物 / 阶段 skill 的关系

| 调用方 | 实际调用 |
| --- | --- |
| `multica-artifact-req-sync` | PRD HTML create-page |
| `multica-artifact-design-sync` / `-backend` / `-frontend` | `publish_design.py` |
| `multica-test-t1-design` | `fetch_page_by_url.py`（`fetch_all` 编排） |

完整矩阵见 [`docs/platform-collaboration.md`](../../../../docs/platform-collaboration.md)。

## Agent Compatibility

- 凭据见 frontmatter；禁止打印密码。
- 外部写入前确认 space、父 pageId、标题。
- 优先 `python scripts/`，不要裸调 REST。
- 与 JIRA 联调时确保 `multica-platform-jira` 可解析（`MULTICA_SKILLS_ROOT` 或同级 `templates/skills/`）。

## Adapting To A New Team

1. 改 `config.yaml`：`confluence.url`、`default_space`、回退 `design_parent_page_id`。
2. 正常流程靠 JIRA 描述中的 Confluence 需求链接定父页面，**无需**每需求改 pageId。
3. 新项目追加 `projects.<JIRA-PREFIX>.confluence_space`。

## 为什么有效

父页面跟 Issue 走，文档天然聚在需求树下；Python CLI 跨平台；platform skill 集中能力，artifact skill 保持薄层。
