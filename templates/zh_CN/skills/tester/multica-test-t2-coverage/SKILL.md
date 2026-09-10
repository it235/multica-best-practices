---
name: multica-test-t2-coverage
description: T2 覆盖率评估：G2 PASS 后对照 diff、契约与 T1 Confluence；增量正文 + Apifox 补场景 + tests/e2e Playwright 入库。不生成 XMind。
version: 1.3.0
metadata:
  orchestrates:
    - multica-platform-confluence
    - multica-platform-jira
    - multica-platform-apifox
---

# Test Coverage T2（覆盖率评估）

仅在 **G2 PASS 之后、T3 之前**。评估「T1 够不够」，**不执行**环境验证。

> 整合自 `ac-coverage-t2-squad`。材料拼接规则见 `multica-test-orchestration`「从评论拼接」。

## 必须 5 项（评论拼接；缺一则中断）

| # | 必须 | 评论中如何算齐 |
| --- | --- | --- |
| 1 | 带编号 AC- 原文 | 评论/描述贴出 AC，或可打开的 Jira/PRD 链接 |
| 2 | T1 Confluence 链接 | **t1-cases** Confluence URL（优先）；或已 import 的 JIRA 用例集 |
| 3 | G2 PASS 证据 | Leader 写明 G2 PASS |
| 4 | 前端+后端变更 | SHA + 文件列表，或 MR/PR 链接 |
| 5 | 实现后 API 契约 | Apifox/OAS 链接，或 **N/A（复用 xxx）** |

| 可选 | 说明 |
| --- | --- |
| T1 设计追溯摘要 | `multica-test-t1-design` design-trace 表 |
| T1 用例集链接 | 已导入测试管理平台的 T1 用例集 URL |
| Leader T1 评审结论 | review Pass 记录（非导入授权） |

缺任一项 **必需** → 输出 orchestration「中断：待人类在 Issue 评论补充」表，**不要**写覆盖率结论。

## 流程

1. 读全评论拼接 5 项；缺失 → 中断名单，停止
2. **必读 T1 产物**：T1 Confluence `t1-cases.md` 链接（评论或 JIRA 描述）；T2 **只写相对 T1 的增量**
3. 对每条 AC-：实现证据（diff/契约）？T1 是否真能验到？是否需新接口用例？
4. 信号映射：新 path/字段 → 接口补例；新页/弹窗 → 功能补例；纯重构 → 回归风险；AC 有而 diff 无 → **实现缺口**
5. **Confluence 落地** + **自动化入库**（见下 §§）→ 回传 T2 链接
6. 输出下述模板。结论只用：`评估完成` 或 `评估 BLOCKED`

补例需回写 T1 Confluence：修订 t1-cases → review → republish。👤 口令后可选 XMind/JIRA 阶段 C（见 t1-design generation-workflow）。

## 自动化入库（T2 · Git）

见 `docs/test-automation-in-repo.md`。**开工先读** Issue 矩阵中各 repo 的 **MULTICA.md §2**。

| 类型 | 路径来源 |
| --- | --- |
| UI Playwright | MULTICA.md `UI E2E`（分仓通常在前端 repo） |
| API manifest | MULTICA.md `API manifest`（通常在后端 repo） |

**合入**：deploy branch；Leader 评论贴 MULTICA 中的路径 + commit SHA。

## Confluence 落地（T2）

**硬规则**：含 **T1 Confluence 链接**；补充 CASE 写**正文**（非仅表格）；**不生成 XMind**。

**本地草稿**：`docs/test/<ISSUE-KEY>/t2-coverage.md`  
**基线**：`multica-platform-confluence/scripts/templates/test-t2-template.md`

```bash
python multica-platform-confluence/scripts/publish_design.py \
  <ISSUE-KEY> docs/test/<ISSUE-KEY>/t2-coverage.md \
  --append-jira --json
```

JIRA 块：`h3. T2 覆盖率评估 (Coverage T2)`。

## Platform 协作

| Platform skill | 本 skill 用途 |
| --- | --- |
| `multica-platform-confluence` | 读 T1 子页；发布 `t2-coverage.md` |
| `multica-platform-jira` | Issue Hub；append 链接 |
| `multica-platform-apifox` | T2 按清单补场景 |

T2 材料主来源仍为 Issue 评论拼接；T1 正文以 **Confluence t1-cases 链接** 为准。

## 输出模板

```markdown
# T2 覆盖率评估 — {JIRA_KEY}

## 结论
**评估完成 | 评估 BLOCKED** — {一句话}

## 材料
- AC 来源 / T1 用例集 / G2 SHA / 变更清单 / 契约或 N/A

## AC 覆盖
| AC- | T1 用例 | 实现证据 | 状态 |
|-----|---------|----------|------|
| | | | 已覆盖 / 假覆盖 / 缺口 / 实现未交付 / 条件用例 |

## 用例补充清单
| ID | 动作 | 必须? | 说明 |
|----|------|-------|------|

## 需新接口用例
- 无 / 有（path+原因）。写入端：multica-platform-apifox

## 回归风险
- …
```

## 为什么有效

T2 只做静态缺口评估，与 T3 运行时验证分离；自动化资产在 T2 入库、T3 执行。
