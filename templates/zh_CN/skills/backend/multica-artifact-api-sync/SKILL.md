---
name: multica-artifact-api-sync
description: 后端产物薄编排：API 契约文档规范，落地调 multica-platform-confluence + multica-platform-jira。用于 @BackendDev 发布契约供前端/测试消费。
metadata:
  orchestrates:
    - multica-platform-confluence
    - multica-platform-jira
    - multica-platform-apifox
  local_draft: "docs/backend/<ISSUE-KEY>/api-contract.md"
---

# Artifact · Backend（薄编排）

## Purpose

**只规定 API 契约写什么、发布前怎么自检**；Confluence 发布、Apifox 同步由 platform skill 封装。

> 本 skill **不含脚本**；实现编码见 `multica-backend-impl`（TDD）。

## Platform 协作

| Platform skill | 本 skill 用途 |
| --- | --- |
| `multica-platform-confluence` | 发布 `api-contract.md` 到 Issue Hub 子页 |
| `multica-platform-jira` | 解析父 pageId；`append-artifact-link` 回写契约链接 |
| `multica-platform-apifox` | `sync_openapi.js` 同步 OpenAPI + Issue tag |

凭据与 CLI 细节**只查 platform skill**；矩阵见 [`docs/platform-collaboration.md`](../../../../../docs/zh_CN/platform-collaboration.md)。

## @BackendDev 标准流程

```text
1. multica-backend-impl        — 读上游 + TDD 实现
2. 写 docs/backend/<ISSUE-KEY>/api-contract.md
3. 自检（见下表）
4. multica-platform-confluence — publish_design.py --append-jira
5. multica-platform-apifox — sync_openapi.js（OpenAPI 增/改/删 + Issue tag；**每次新建 AI 分支**，见 platform-apifox `openapi-branch-workflow.md`）
6. 回传 Confluence + Apifox 同步摘要（含 AI 分支名）给 Leader
```

## 父页面（Issue Hub）

与 `multica-artifact-design-sync` 相同：JIRA 描述中 **Confluence 需求页** 为父页面；API 契约发布为其**子页面**。

## API 契约规范（发布前自检）

本地草稿：`docs/backend/<ISSUE-KEY>/api-contract.md`  
基线：`multica-platform-confluence/scripts/templates/backend-api-template.md`

| 章节 | 必填 | 内容要求 |
| --- | --- | --- |
| **文档头部** | 是 | 创建者、时间、版本、状态、JIRA、上游 PRD、架构设计链接 |
| **概述** | 是 | 范围；与架构实现步骤对应 |
| **端点清单** | 是 | API-ID · 方法 · 路径 · 对应 BR-/AC- |
| **端点详情** | 是 | 请求/响应 schema、错误码、鉴权 |
| **通用约定** | 推荐 | 分页、幂等、时间格式等 |
| **数据模型** | 涉及时 | 实体/字段变更 |
| **TDD / 测试映射** | 是 | API-ID → 单元测试覆盖 |
| **修订记录** | 是 | 版本递增 |

Breaking change → **版本 +1**，修订记录说明，通知 Leader 与 @FrontendDev。

## 落地（platform skill）

```bash
pip install -r multica-platform-confluence/scripts/requirements.txt
python multica-platform-confluence/scripts/publish_design.py \
  <ISSUE-KEY> docs/backend/<ISSUE-KEY>/api-contract.md \
  --append-jira --json
```

JIRA 追加块标题建议：`h3. API 契约 (API Contract)`（`append-artifact-link --section "API 契约 (API Contract)"`）。

## Apifox 同步（platform skill）

契约发布后，将 `openapi.json`（与契约同目录或团队约定路径）同步到 Apifox：

```bash
set APIFOX_ACCESS_TOKEN=<token>
set APIFOX_PROJECT_ID=<projectId>

node multica-platform-apifox/scripts/sync_openapi.js \
  --file docs/backend/<ISSUE-KEY>/openapi.json \
  --issue <ISSUE-KEY> \
  --branch ai/<ISSUE-KEY>-openapi-<YYYYMMDD> \
  --json
```

**每次同步必须 `--branch` 新建 AI 分支**（禁止省略、禁止直写 main）。步骤见 `multica-platform-apifox/references/openapi-branch-workflow.md`。

接口增/改/删与 Issue tag 由 platform skill 处理；Apifox 项目链接写入契约头部修订记录。

## 用法（角色侧）

```text
产出 API 契约，按 multica-artifact-api-sync 规范写 api-contract.md，
自检后 platform 发布到 Confluence 并回传链接。
```

## 为什么有效

契约挂在需求 Confluence 树下，与 PRD/架构设计同树；薄编排 + TDD 在 impl skill，职责清晰。
