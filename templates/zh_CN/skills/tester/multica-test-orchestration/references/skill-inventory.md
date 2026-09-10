# Tester Skill 交叉引用

> 整合自 `acceptance-verifier-squad/INVENTORY.md`。Multica **按 skill 名称挂载**，路径见 `templates/skills/` 分类目录。  
> **禁止**在 Agent 指令中写死 `*-squad` 旧名或本机绝对路径；只引用 `multica-*` skill 名。

## 挂载顺序（@Tester）

1. **`multica-test-orchestration`** — 跨阶段编排（首选）
2. 按阶段 Read 子 skill（见下表）
3. Platform / Reviewer 由子 skill 声明 `metadata.orchestrates`

## 阶段 → Skill（原 squad 对照）

| 阶段 | 现 Skill | 原 squad | 说明 |
| --- | --- | --- | --- |
| 编排 | `multica-test-orchestration` | acceptance-verifier-squad | 路由、门禁、skill-inventory |
| T1 设计 | `multica-test-t1-design` | test-case-generator-squad + ac-design-trace-squad | 内容+脚本合一 |
| T1 审核 | `multica-review-test` | test-case-review-squad | reviewer/；只审不导入 |
| T1 KB | `团队知识库（可选）` | 团队知识库问答（可选平台 skill） | platform/ |
| T1/T2 Apifox 写 | `multica-platform-apifox` | apifox-test-case-supplement-squad | 场景补充，非 T3 跑批 |
| T2 | `multica-test-t2-coverage` | ac-coverage-t2-squad | 缺口评估 |
| T3 UI | `multica-test-t3-ui-automation` | functional-ui-auto-squad | pytest UI |
| T3 接口 | `multica-test-t3-api-automation` | software-development | 编排+校验 |
| T3 跑批 CLI | `multica-platform-apifox` | （原 automation CLI） | `run_apifox.py` |

## 原 squad 文件 → 现 references 映射（T1 / Apifox / Review）

| 原路径（generator / review / apifox） | 现路径 |
| --- | --- |
| `test-case-generator-squad/SKILL.md` Step 0.5 | `multica-test-t1-design/references/generation-workflow.md` |
| `…/SKILL.md` Output Format | `…/references/output-format.md` |
| `…/SKILL.md` 可执行性/权限 | `…/references/executability-and-permissions.md` |
| `…/SKILL.md` 维度/规模 | `…/references/coverage-dimensions.md` |
| `…/references/coverage-checklist.md` | `…/references/coverage-checklist.md`（同版） |
| `…/references/test-case-template.md` | `…/references/test-case-template.md`（同版） |
| `…/references/data-sources.md` | `…/references/data-sources.md` + platform skills |
| `…/MULTICA.md` | `…/references/agent-instructions.md` |
| `…/scripts/*` | `…/scripts/*`（fetch 已迁 platform） |
| `ac-design-trace-squad/SKILL.md` | `…/references/design-trace.md` |
| `test-case-review-squad/checklist.md` | `multica-review-test/checklist.md` |
| `test-case-review-squad/AGENT_INSTRUCTIONS.md` | `multica-review-test/references/agent-instructions.md` |
| `apifox-test-case-supplement-squad/SKILL.md` | `multica-platform-apifox/references/supplement-workflow.md` |
| `…/reference.md` | `…/references/reference.md` |
| `…/MULTICA.md` | `…/references/agent-instructions.md` |
| `…/CHANGELOG.md` | `…/references/CHANGELOG.md` |
| `团队知识库问答（可选平台 skill）/SKILL.md` | `团队知识库（可选）/SKILL.md` |

## T1 关键 references

| 文件 | 用途 |
| --- | --- |
| `multica-test-t1-design/references/generation-workflow.md` | 两阶段、口令、测试管理平台、Step 0.5 |
| `multica-test-t1-design/references/output-format.md` | JSON 1:1、覆盖自查表 |
| `multica-test-t1-design/references/executability-and-permissions.md` | 权限识别顺序、可执行性自检 |
| `multica-test-t1-design/references/coverage-dimensions.md` | 维度与规模 |
| `multica-test-t1-design/references/multimodal-content.md` | HTML/图片 |
| `multica-review-test/checklist.md` | 审核勾选项 |

## 禁止混用

- T1 导入：**仅** `multica-test-t1-design/scripts/import_to_tracker.py`（Tester 执行）
- T1 审核：**仅** `multica-review-test`（TestReviewer；永不 import）
- T3 UI：**禁止** xmind-ui-automation / playwright.git
- Apifox 基址：企业私有化（见 platform-apifox config），非 app.apifox.com
- **禁止**挂载无 `multica-` 前缀的旧 squad 名（`test-case-generator-squad` 等）

## Agent 指令入口

| Skill | 可复制指令 |
| --- | --- |
| 编排 | `multica-test-orchestration/references/agent-instructions.md` |
| T1 | `multica-test-t1-design/references/agent-instructions.md` |
| 审核 | `multica-review-test/references/agent-instructions.md` |
| Apifox 补充 | `multica-platform-apifox/references/agent-instructions.md` + `supplement-workflow.md` |
