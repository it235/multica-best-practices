---
name: multica-artifact-req-sync
description: PRD 产物编排：默认把 PRD 保存为仓库内 Markdown 并回传稳定引用；团队需要时可显式切换到外部平台适配器。
metadata:
  default_mode: local
  orchestrates:
    local: []
    external:
      - multica-platform-confluence
      - multica-platform-jira
---

# Artifact · Requirement Sync（编排）

## Purpose

**PRD 专用编排 skill**——负责把 PRD 变成下游可读取的稳定引用，不负责生成 PRD 内容。默认使用零依赖的仓库内 Markdown；只有团队明确要求外部平台时，才调用 platform skill。

| 模式 | 适用场景 | 稳定引用 |
| --- | --- |
| `local`（默认） | 不需要 Confluence / JIRA / 钉钉等外部平台 | 仓库相对路径 `artifacts/<issue-id>/prd.md` |
| `external`（显式启用） | 团队已有需求/任务平台并希望同步 | 平台页面或任务链接 |

> 内容结构由 `multica-requirement-analysis` 负责；本 skill 只编排落地。

## @ProductManager 标准流程（默认 local）

```text
1. multica-requirement-analysis  — 结构化 PRD
2. multica-artifact-req-sync     — 本 skill：保存 Markdown，返回稳定相对路径
```

## Workflow A：仓库内 Markdown（默认、推荐）

1. 把结构化 PRD 写入临时 Markdown 文件。
2. 运行本地发布脚本：

```bash
bash scripts/publish-local.sh \
  --issue-id <ISSUE-ID> \
  --input <PRD.md> \
  --root artifacts
```

3. 回传脚本输出的仓库相对路径，例如 `artifacts/GOO-3/prd.md`。下游必须使用该引用，不靠搜索定位。

本模式不读取凭据、不发网络请求、不创建外部任务。更新同一需求时覆盖同一路径，并在 PRD 修订记录中写明版本；PRD 内容变化后，下游门禁按 Squad 规则失效并重判。

## Workflow B：外部平台（可选）

只有 Issue 或团队配置明确要求外部同步时，才调用 `multica-platform-confluence` / `multica-platform-jira`：

```bash
export MULTICA_SKILLS_ROOT="/path/to/templates/skills"   # Multica 按名挂载时建议设置
bash scripts/publish-prd.sh --project AAI --summary "..." --html-file prd.html \
  -- --need-user <user> --background "..." ...
```

外部平台失败时不得静默假装成功：若 Issue 未强制外部落地，可降级到 local 并明确回传相对路径和降级原因；若强制要求外部平台，则标记 BLOCKED。

## 配置

- 默认无需配置。
- 本地根目录可用 `--root` 指定，默认 `artifacts`；必须使用仓库相对路径，禁止绝对路径和 `..`。
- 外部模式配置仍由 `multica-platform-confluence/config.yaml` / `multica-platform-jira/config.yaml` 管理；本目录 `config.yaml` 仅为旧团队兼容。

## 用法（角色侧）

```text
先用 multica-requirement-analysis 结构化 PRD，
再用 multica-artifact-req-sync 落地并回传稳定引用；未明确要求外部平台时使用 local 模式。
```

## 为什么有效

“稳定引用”不等于“外部平台链接”。默认仓库路径让小队零凭据即可运行；外部平台仍作为可插拔适配器，角色提示词和 PRD 内容规范无需随落地方式变化。
