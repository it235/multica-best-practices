---
name: multica-artifact-frontend
description: 前端产物薄编排：实现说明文档规范，落地调 multica-platform-confluence + multica-platform-jira。用于 @FrontendDev 发布交互/页面对照说明。
metadata:
  orchestrates:
    - multica-platform-confluence
    - multica-platform-jira
  local_draft: "docs/frontend/<ISSUE-KEY>/impl-spec.md"
---

# Artifact · Frontend（薄编排）

## Purpose

**只规定前端实现说明写什么、发布前怎么自检**；Confluence 发布、JIRA 回写由 platform skill 封装。代码在真实仓库，本文档供评审 / 测试 / Leader 对照。

> 本 skill **不含脚本**；编码与体验见 `multica-frontend-impl`。

## Platform 协作

| Platform skill | 本 skill 用途 |
| --- | --- |
| `multica-platform-jira` | 读 Issue / 回写 impl-spec 链接 |
| `multica-platform-confluence` | 发布 `impl-spec.md` 到 Issue Hub 子页 |
| `multica-platform-figma` | 读设计链接（上游由 Designer / Issue 提供） |

凭据与 CLI 细节**只查 platform skill**。

## @FrontendDev 标准流程

```text
1. multica-frontend-impl       — 读上游（PRD/架构/UI/API）
2. 写 docs/frontend/<ISSUE-KEY>/impl-spec.md（开工前或实现中更新）
3. 自检（见下表）
4. multica-platform-confluence — publish_design.py --append-jira
5. 实现页面/组件 + 测试
6. 回传 Confluence 链接 + 代码证据给 Leader
```

## 父页面（Issue Hub）

JIRA 描述中 **Confluence 需求页** 为父页面；前端实现说明发布为其**子页面**（与架构设计、API 契约并列）。

## 实现说明规范（发布前自检）

本地草稿：`docs/frontend/<ISSUE-KEY>/impl-spec.md`  
基线：`multica-platform-confluence/scripts/templates/frontend-impl-template.md`

| 章节 | 必填 | 内容要求 |
| --- | --- | --- |
| **文档头部** | 是 | 创建者、时间、版本、状态、JIRA、PRD、架构、UI、API 链接 |
| **页面与路由** | 是 | 页面 · 路由 · 入口 · AC- |
| **交互与状态** | 是 | 操作/反馈；**空态/加载/异常/无权限** |
| **组件映射** | 是 | UI 区域 · 组件 · 复用/新建 |
| **API 对接** | 涉及时 | API-ID · 调用时机 · 错误 UX |
| **表单与校验** | 涉及时 | 规则 · 提示文案 · BR- |
| **体验与无障碍** | 按需 | 响应式、键盘、性能感知 |
| **Mock 策略** | 后端未就绪时 | Mock 位置与切换条件 |
| **验证计划** | 是 | 组件/手动/E2E · AC- |
| **修订记录** | 是 | 版本递增 |

自检 FAIL → 先补文档，不调 platform。

## 落地（platform skill）

```bash
pip install -r multica-platform-confluence/scripts/requirements.txt
python multica-platform-confluence/scripts/publish_design.py \
  <ISSUE-KEY> docs/frontend/<ISSUE-KEY>/impl-spec.md \
  --append-jira --json
```

JIRA 追加块：`h3. 前端实现说明 (Frontend Implementation)`。

## 用法（角色侧）

```text
按 multica-artifact-frontend 规范写 impl-spec.md，
自检后 platform 发布到 Confluence 并回传链接。
```

## 为什么有效

把「交互与状态」从代码里抽成可评审文档，挂需求树下；与后端契约、架构设计同 Hub，下游不迷路。
