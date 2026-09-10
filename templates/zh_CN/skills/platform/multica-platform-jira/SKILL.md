---
name: multica-platform-jira
description: JIRA 读写：Issue 查询、Confluence 链接解析、Story 创建、流转、排期、描述回写、钉钉。平台 skill，与 Confluence 解耦。跨平台优先 jira_cli.py。
metadata:
  credentials:
    priority:
      - JIRA_USERNAME / JIRA_PASSWORD
      - JIRA_USERNAME / JIRA_PASSWORD
      - JIRA_USER / JIRA_PASS
---

# Platform · JIRA

## Platform 协作

本 skill 为 **platform 层**；供 artifact / Tester T1 等按名调用。读：`get_issue.py`、`get-confluence-url`；写：Story / append / transition。

## Purpose

JIRA **读 + 写**能力：查询 Issue、从描述解析 **Confluence 需求页**（Issue Hub）；写入 Story、流转、排期、描述追加、钉钉。

> **跨平台**：优先 `python scripts/jira_cli.py`（Windows / macOS / Linux）；`jira.sh` 为 Unix 全功能封装，非 artifact 流程必需。

## Issue Hub

JIRA Issue 描述（及 remote link）中的 **第一个 Confluence pageId** = 本需求的 PRD/需求正文页。

- 下游文档产物（技术设计等）以该页为 **Confluence 父页面**（由 `multica-platform-confluence` `publish_design.py` 自动解析）。
- Leader / 下游读 PRD：本 skill 解析链接 → Confluence `fetch_page.py`。
- **关联 Issue**：`get_issue.py` 输出 `linked_issues`；开工前必读规则见 [`references/upstream-read.md`](references/upstream-read.md) 与 `docs/multi-repo-and-issue-links.md` §2。

## Files

```text
multica-platform-jira/
├── SKILL.md
├── config.yaml
├── .env.example
└── scripts/
    ├── jira_cli.py          # 跨平台 CLI（推荐）
    ├── get_issue.py         # Issue JSON（Tester fetch_all）
    ├── jira.sh              # Unix 全功能封装（可选）
    ├── lib/jira_client.py
    └── requirements.txt
```

## Read（跨平台 CLI）

```bash
pip install -r scripts/requirements.txt

# 完整 Issue JSON（含 Confluence/Figma 链接、附件、linked_issues）— Tester fetch_all 使用
python scripts/jira_cli.py get-issue --url "https://jira.../browse/PROJ-123" --output data/jira.json
# 或直接
python scripts/get_issue.py --url "https://jira.../browse/PROJ-123" --output data/jira.json

# 含关联 Issue 一层描述与链接（迭代/依赖需求）
python scripts/get_issue.py --url "https://jira.../browse/PROJ-123" --with-linked -o data/jira-full.json

# Issue 中的 Confluence 链接 / pageId
python scripts/jira_cli.py get-confluence-url <ISSUE-KEY> --json

# 作为文档产物父页面的 pageId（第一个 Confluence 链接）
python scripts/jira_cli.py resolve-parent-page-id <ISSUE-KEY>
```

Unix 可选：`bash scripts/jira.sh get-issue <ISSUE-KEY>`、`bash scripts/jira.sh search ...`

## Write · 产物链接回写

```bash
# 通用 Wiki 块追加
python scripts/jira_cli.py append-description <ISSUE-KEY> "h3. 标题\n* [链接|url]\n"

# 结构化产物链接（设计 / API 等）
python scripts/jira_cli.py append-artifact-link <ISSUE-KEY> \
  --section "设计文档 (Design Document)" \
  --title "xxx [AI]" \
  --url "http://confluence.../pageId=..." \
  --source design.md
```

`publish_design.py --append-jira` 会在发布成功后自动调用等价逻辑。

## 与产物 / 阶段 skill 的关系

| 调用方 | 实际调用 |
| --- | --- |
| `multica-artifact-req-sync` | create-story / transition / … |
| `multica-artifact-design-sync` | get-confluence-url、append-artifact-link（发布由 confluence skill） |
| `multica-artifact-api-sync` / `-frontend` | append-artifact-link |
| `multica-test-t1-design` | `get_issue.py` / `get-issue`；`import_to_tracker.py` 仍在本 skill | 读已迁入 platform |

完整矩阵见 [`docs/platform-collaboration.md`](../../../../../docs/zh_CN/platform-collaboration.md)。

## Adapting To A New Team

改 `config.yaml`：`jira.url`、`projects.*.fields`、钉钉映射等。

## 为什么有效

Issue 自带 JIRA 编号与 Confluence 需求链接，父页面无需写死在角色提示词；Python CLI 避免 Windows 上依赖 bash。
