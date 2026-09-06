---
name: multica-test-t1-design
description: T1 测试设计：AC↔设计追溯、用例模板与覆盖自检、Confluence 主副本、口令后 XMind/JIRA、Apifox 场景与 e2e 规划。整合 ac-design-trace + test-case-generator-squad。
version: 3.3.0
metadata:
  orchestrates:
    - multica-platform-jira
    - multica-platform-confluence
    - multica-platform-figma
    - multica-platform-apifox
  origin:
    - ac-design-trace-squad
    - test-case-generator-squad
---

# Test Design（T1 测试设计 · 内容 + 落地）

## 定位

**T1 唯一 skill**：追溯 → 用例 → **Confluence 全文** → 审核 →（👤 口令后）XMind/JIRA；并行 Apifox + 自动化规划。  
**不用于 T2/T3**——T2 见 `multica-test-t2-coverage`；T3 见 `-t3` + `multica-test-orchestration`。

| 层 | Skill | 职责 |
| --- | --- | --- |
| 编排 | `multica-test-orchestration` | 跨阶段路由；自动化入仓见 `references/automation-assets-lifecycle.md` |
| **T1** | **本 skill** | 内容 + Confluence + 口令后 XMind/JIRA |
| 平台 | `multica-platform-*` | 读上游；Apifox 写场景 |
| 审核 | `multica-review-test` | 审 Confluence；只审不 import |

> **三阶段交付**：阶段 A **仅 Confluence**（**不生成 XMind**）；👤 口令后阶段 C 才 XMind + JIRA。详见 [`references/generation-workflow.md`](references/generation-workflow.md)。

## Platform 协作

| Platform skill | 本 skill 用途 |
| --- | --- |
| `multica-platform-jira` | `fetch_all` → `get_issue.py`；口令后 `import_to_tracker.py`（团队自备，见 references/import-contract.md） |
| `multica-platform-confluence` | 采集 `fetch_page`；**发布** `t1-cases.md`（见 § Confluence 落地） |
| `multica-platform-figma` | `fetch_all` → `fetch_file.py` |
| `multica-platform-apifox` | T1 并行写接口场景 |
| 团队知识库（可选） | Step 0.5 术语/入口（用法二分；本仓库未随附，按所用平台接入） |

凭据：`JIRA_USERNAME / JIRA_PASSWORD` 优先 → 见 platform skill + [`data-sources.md`](references/data-sources.md)。

## references/ 索引

| 文件 | 用途 |
| --- | --- |
| [`generation-workflow.md`](references/generation-workflow.md) | **两阶段、口令、测试管理平台 命名/校验、步骤/优先级、去重/合并** |
| [`executability-and-permissions.md`](references/executability-and-permissions.md) | **权限识别顺序、双目标、模块命名、生成后自检** |
| [`output-format.md`](references/output-format.md) | **JSON 1:1、generated_summary、覆盖自查表、Output Delivery** |
| [`multimodal-content.md`](references/multimodal-content.md) | HTML/图片 Read 与融合理解 |
| [`agent-instructions.md`](references/agent-instructions.md) | 可复制 Agent 指令 |
| [`design-trace.md`](references/design-trace.md) | AC ↔ 设计追溯 |
| [`test-case-template.md`](references/test-case-template.md) | 功能用例字段 |
| [`coverage-dimensions.md`](references/coverage-dimensions.md) | 维度选择、规模缩放、覆盖矩阵、XMind |
| [`coverage-checklist.md`](references/coverage-checklist.md) | 生成前自检清单 |
| [`web-ui-checkpoints.md`](references/web-ui-checkpoints.md) | Figma → UI 测试点 |
| [`api-testing-guide.md`](references/api-testing-guide.md) | 接口场景模式 |
| [`data-sources.md`](references/data-sources.md) | 采集编排与凭据 |

## T1 流程

### Step 0 — 读 MULTICA.md（自动化路径）

Issue 仓库矩阵 → 每个 repo Read 根目录 **MULTICA.md §2**（分仓各一份；同仓一份须完整）。缺则 BLOCKED。

### Step 0.5 — 知识库（Step 0.5）

团队知识库问答脚本（可选接入）→ `--health` + 问答。**用法二分**：操作桶进步骤，规则桶不当 AC。见 `generation-workflow.md`。

### Step 1 — 设计追溯

[`design-trace.md`](references/design-trace.md) → 追溯表写入覆盖报告。

### Step 2 — 采集

```bash
python scripts/fetch_all.py --jira-url "http://jira.../browse/PROJ-123" -o ./data
```

多模态：[`multimodal-content.md`](references/multimodal-content.md)。

### Step 3–4 — 用例 + 自检

按 `test-case-template.md` + `generation-workflow.md` + `output-format.md` → 本地 JSON（工作文件）；`coverage-checklist.md` 自检。**不写 XMind**。

### Step 5 — 阶段 A：Confluence + Apifox 并行

- 将 **完整用例正文** 写入 `docs/test/<ISSUE-KEY>/t1-cases.md`（模板见 platform-confluence `test-t1-template.md`）
- **Confluence 落地**（见下 §）→ 回传链接
- API 契约就绪 → `multica-platform-apifox` 按契约补场景（AI 分支；写 manifest 规划节）
- → `multica-review-test`（审 **Confluence**）
- 交付语：`状态：待人工审核（Confluence 已更新，未 XMind/未导入 JIRA）`

### Step 6 — 阶段 C：XMind + JIRA（👤 明确口令后）

1. `generate_xmind.py` ← 最新 JSON（与 Confluence 一致）
2. `import_to_tracker.py`（团队自备，接口见 `references/import-contract.md`）
3. republish Confluence 状态「已导入 JIRA」+ 用例集链接

## Confluence 落地（T1 · 主副本）

**父页面**：JIRA Issue Hub（PRD 需求页）**子页面**。

**本地草稿**：`docs/test/<ISSUE-KEY>/t1-cases.md`  
**基线**：`multica-platform-confluence/scripts/templates/test-t1-template.md`

须含 **每条 CASE 步骤/预期正文**、Apifox 节、UI e2e 规划（路径写 **MULTICA.md §2**，非硬编码）。T1/T2 **不生成 XMind**。

**发布**：

```bash
python multica-platform-confluence/scripts/publish_design.py \
  <ISSUE-KEY> docs/test/<ISSUE-KEY>/t1-cases.md \
  --append-jira --json
```

JIRA 块：`h3. T1 测试用例 (Test Cases T1)`。

## Apifox（T1 并行）

契约发布后：读 API 契约 → `multica-platform-apifox` 补场景（AI 分支）→ Confluence 记录 branch/scenario → manifest 路径见 **MULTICA.md §2**。

## Files

```text
multica-test-t1-design/
├── SKILL.md
├── config.local.env.example
├── references/
└── scripts/
```

## 为什么有效

T1 内容与脚本合一；**generation-workflow** + **output-format** 保留原版 generator 硬规则；platform 统一采集 REST。
