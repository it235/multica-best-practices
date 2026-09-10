---
name: multica-test-orchestration
description: Tester T1/T2/T3 编排与门禁：子 skill 路由、Issue 评论拼接材料、BLOCKED 中断名单。整合 acceptance-verifier-squad；@Tester 首选挂载。
version: 1.0.0
metadata:
  orchestrates:
    - multica-test-t1-design
    - multica-test-t2-coverage
    - multica-test-t3-ui-automation
    - multica-test-t3-api-automation
    - multica-platform-jira
    - 团队知识库（可选）
    - multica-platform-apifox
---

# Test Orchestration（验收标准验证者 · 编排）

你对「需求到底实现没有」负责。测试左移，分 **T1 / T2 / T3**。T3 必须等待 DevOps **G2.5 PASS** 后再执行自动化。

> **本 skill 不属于 T1/T2/T3 任一阶段**，是跨阶段编排入口：路由、评论拼接、BLOCKED、T3 合并裁决。整合自 `acceptance-verifier-squad`；方法细节在各 `-t1`/`-t2`/`-t3` 子 skill。

## Platform 协作

| Platform skill | 本 skill 用途 |
| --- | --- |
| `multica-platform-jira` | T2/T3 前读 Issue 全评论（`get-issue` / 等价） |
| `团队知识库（可选）` | T1 Step 0（经 `multica-test-t1-design`） |
| `multica-platform-apifox` | T1 并行场景 + T3 跑批（经 t1-design / t3-api-automation） |

T1 采集（JIRA / Confluence / Figma）经 `multica-test-t1-design` → platform-jira / confluence / figma。凭据与 CLI **只查 platform skill**。

## 子 skill 路由（必须 Read 后再做）

| 阶段 | Skill | 产出 |
| --- | --- | --- |
| 编排/门禁 | 本文件 | 阶段卡、BLOCKED 原因 |
| T1 测试设计 | `multica-test-t1-design` | Confluence 用例全文 + Apifox 场景 + e2e 规划 |
| T1 质检 | `multica-review-test` | 审 Confluence；👤 口令后 XMind/JIRA |
| 并行接口场景 | `multica-platform-apifox` | 按 API 契约补场景（AI 分支） |
| T2 | `multica-test-t2-coverage` | Confluence 增量 + Apifox + MULTICA §2 e2e 入库 |
| T3 接口 | `multica-test-t3-api-automation` → `multica-platform-apifox` | Apifox 日志 + 参与总报告 |
| T3 UI | `multica-test-t3-ui-automation` | pytest+Playwright 1:1 执行 |
| T3 裁决 | 编排合并两侧证据 | 唯一 PASS/FAIL/BLOCKED |

智能体可复制指令见 [`references/agent-instructions.md`](references/agent-instructions.md)。  
Skill 交叉引用见 [`references/skill-inventory.md`](references/skill-inventory.md)；T3 合并报告见 [`references/t3-merge-report.md`](references/t3-merge-report.md)；**自动化入仓**见 [`references/automation-assets-lifecycle.md`](references/automation-assets-lifecycle.md)。

## 任务卡（缺则停止）

```text
stage: T1 | T2 | T3 | parallel-api
issue:                  # Multica 与/或 Jira Key
ac_source:              # Issue/PRD 带编号 AC- 原文位置
```

T2 / T3 材料：**只从本 Issue 描述 + 全部评论（含附件名）拼接**。拼不齐 → **中断**，输出缺失名单，等人类在评论补齐后再继续。禁止臆造，禁止用本机 mock / 未在评论出现的 URL 顶替。

## 从评论拼接（强制）

进入 T2 / T3 / parallel-api 前，必须 `jira_cli.py get-issue --comments`（或等价读全评论），按下面识别并填任务卡。

| 字段 | 评论里出现任一即可 |
| --- | --- |
| `g2_pass` | Leader 明确写 G2 PASS / G2 汇合判门 PASS |
| `g2_sha` / 变更 | 合入 SHA、前后端 commit、变更文件表、或 MR/PR 链接 |
| `api_contract` | Apifox/OAS 链接，或明文 **N/A + 复用哪条接口/链路** |
| `g25_pass` | Leader/DevOps 明确 **G2.5 PASS**；仅「G2.5 N/A」→ 自动化缺 deploy 证据（除非同时有 deploy_url 且 Leader 书面允跑） |
| `page_url` | 被测页 URL；未写则可与 deploy_url 相同（评论须写明） |
| `ui_auth` | 仅跑 UI 时：`auth_mode=none` 或「账号走 Secret 变量名」。**禁止采用评论里的明文密码** |
| `apifox_project_id` / `environment_id` / `scenario_ids` | 数字 ID 或场景链接；契约 N/A 且本迭代无接口自动化 → 三项标 **N/A（非缺失）** |

冲突时：**较晚的 Leader 评论优先**。只出现分支名、没有 SHA/文件表/MR 链接 → 变更项仍算缺失。

### 缺失则中断（输出给人类）

```markdown
## 中断：待人类在 Issue 评论补充

阶段: T2 | T3
Issue: {id}

### 已从评论拼接
- {字段}: {摘录来源评论摘要}

### 缺失名单（请按右列格式回评论）
| 缺失项 | 请补充 |
|--------|--------|
| g2_sha / 变更文件或 MR 链接 | 例：SHA + 文件列表，或 GitLab MR URL |
| api_contract | Apifox/OAS 链接，或：N/A（复用 xxx） |
| g25_pass | G2.5 PASS 或明确未过 |
| deploy_url | 可访问的环境 URL |
| apifox_project_id | 数字，或 N/A |
| apifox_environment_id | 数字或环境名，或 N/A |
| apifox_scenario_ids | 场景 ID 列表，或 N/A |

补齐后回复「继续 T2」或「继续 T3」。
```

## 门禁（不可协商）

- **不因为**能编译、单测过了、实现者说没问题 **就判通过**
- **不把 BLOCKED 转成 PASS**
- **G2.5 未 PASS 时禁止 T3 自动化**；禁止用本地 mock 替代部署环境
- **G2.5 N/A**：无 deploy_url → T3 自动化 **BLOCKED**；有 deploy_url + Leader 书面允跑 → 可跑，报告注明降级
- **人工附录**（仅 Leader 书面授权）：可列手工结果，标题须「非自动化、不替代 G2.5」；**不得**因此把整单自动化判 PASS（见 `t3-merge-report.md`）
- T1 导入：必须 `multica-review-test` 非 Block，且用户/Leader **明确导入口令**
- T2 结论只允许「评估完成 / 评估 BLOCKED」，**禁止**写成验收 PASS/FAIL
- 接口用例不导入 JIRA

## T1 流程

1. 锁定 Issue + AC- 原文
2. `multica-test-t1-design` — Confluence **全文** t1-cases（**不 XMind**）+ 并行 Apifox（契约就绪后）
3. `multica-review-test` — 审 Confluence
4. 👤 口令后：XMind → `import_to_tracker.py`（阶段 C）
5. 规划 e2e / API manifest 路径（**MULTICA.md §2**；T2 落库）

Leader 判 T1 门（Confluence 链接 + Apifox 摘要）。

## T2（仅 G2 PASS 之后）

凑齐评论材料 → `multica-test-t2-coverage`：Confluence 增量 + Apifox 补场景 + **Playwright 写入 MULTICA §2 e2e 路径** + manifest 更新 → commit deploy branch。

## T3（仅 G2.5 PASS + URL 之后）

先凑齐 `g25_pass` + `deploy_url`。

| 条件 | 执行 |
| --- | --- |
| 已确认用例 + page_url + **e2e 脚本在 deploy branch**（路径见 MULTICA §2） | `multica-test-t3-ui-automation` |
| 契约非 N/A + manifest 或 Apifox 三 ID 齐 | `multica-test-t3-api-automation` |
| 都齐 | 都跑，再合并一份 AC 报告 |
| 该跑的一侧材料缺 | 该侧中断；另一侧可跑。有 AC 只能靠缺失侧验证 → **整单不得 PASS** |

无 UI 通道时 Apifox 材料仍按契约要求；无接口通道时 Apifox 三 ID 标 N/A **不算缺失**。

**禁止**使用 `xmind-ui-automation`、`playwright.git`、`req-figma-ui-automation` 作为 T3 UI 前置。

合并报告模板：[`references/t3-merge-report.md`](references/t3-merge-report.md)。**FAIL/ERROR 分诊**：[`references/t3-failure-triage.md`](references/t3-failure-triage.md)（**@Tester** 负责；用例问题自修，产品问题派 FE/BE）。报告对应 G3。

## 为什么有效

编排与内容 skill 分离：Tester 只挂载本 skill 即知阶段路由与硬门禁，子 skill 可独立演进。
