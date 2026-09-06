# 测试产物专业评审（TestReviewer）

本 skill 提供对 **测试产物** 的结构化评审。整合自 **`test-case-review-squad`**。

## 什么时候用

| 阶段 | 评审对象 | 结论模型 |
| --- | --- | --- |
| **T1 阶段 A** | `test_cases.json` + `test_cases_{KEY}.xmind` + 设计追溯 | **Block / Revise / Pass** |
| **T2** | `multica-test-t2-coverage` 输出 | 评估完成 / 评估 BLOCKED |
| **T3** | 合并报告 + UI mapping + Apifox JSON | **PASS / FAIL / BLOCKED**（Leader 门禁） |

**Pass ≠ 导入 JIRA 授权。** 本 role **永不**调用 `import_to_tracker.py`。

智能体指令见 [`references/agent-instructions.md`](references/agent-instructions.md)。

---

## T1 审核（Block / Revise / Pass）

### 输入（缺主交付 → Block）

| 必需 | 说明 |
| --- | --- |
| 功能用例 JSON | `jira_key` + `functional[]` |
| XMind | `test_cases_{JIRA_KEY}.xmind` |
| 需求依据 | Jira AC / 已采集 PRD |

**材料源（有其一即可还原 functional，不必要求评论里贴 JSON 路径）：**

- 功能用例 JSON（`jira_key` + `functional`），或
- XMind：`test_cases_{JIRA_KEY}.xmind`（含 Issue 附件），或
- 已导入的 JIRA/测试管理平台 用例集（步骤 + 预期）

**用例源与需求依据都缺** → Block，列出缺失项后停止。

### 审核顺序（不可跳步）

1. **锁定材料** — Key 与 XMind 文件名一致；缺材料 → Block
2. **机械校验** — steps/expected 等长；无 P0；无 wiki/TBD/缺少Figma/XXX；module 用 `/` 分层
3. **需求对齐** — AC 对照表；假覆盖；**用法二分**（操作桶应进步骤，规则桶不得进 expected）
4. **可执行性** — **P1 全审**；P2/P3 **抽样**（至少每模块 1 条 P2 + 1 条 P3，大模块可增抽）；检查入口路径、权限语义、造数、预期可判定、优先级 P1/P2/P3
5. **结论** — Block | Revise | Pass + 强制输出模板

详细勾选项见 [`checklist.md`](checklist.md)。

### 严重级别

| 级别 | 典型 |
| --- | --- |
| **Critical** | 缺交付；结构崩坏；大面积占位；KB 规则当 AC；写死密码 |
| **Major** | AC 缺口；假覆盖；无入口；P0 或优先级错乱 |
| **Minor** | 标题啰嗦；个别预期可更贴文案 |

| 结论 | 条件 |
| --- | --- |
| **Block** | Critical 或材料不足 |
| **Revise** | 无 Critical，有 Major |
| **Pass** | 无 Critical；Major=0（或用户书面接受）；可有 Minor |

Revise 且用户授权修改 → 改 JSON → `multica-test-t1-design` 的 `generate_xmind.py` → **再审一轮**；仍不 import。

### T1 输出模板（强制）

```markdown
# 用例审核报告 — {JIRA_KEY}

## 结论
**{Block|Revise|Pass}** — {一句话}

## 材料
- JSON: {path}
- XMind: {path}
- 需求依据: {摘要}
- 功能用例数: {n}

## Critical / Major / Minor
- …

## AC 覆盖对照
| 验收点 | 覆盖用例 | 状态 |
| --- | --- | --- |

## 知识库/历史使用抽查
- 操作桶写入步骤: 是/否/部分
- 规则扩写: 无/有

## 导入建议
- Block/Revise: 禁止导入；先修订并重生 XMind
- Pass: 可提交人工确认；**本 skill 不执行导入**。确认后对 Tester 下达「审核通过，导入 JIRA」
```

---

## T2 / T3（Leader 门禁风格）

### T2 额外检查

- [ ] 材料 5 项在评论中可追溯
- [ ] 未写成「测试报告 PASS/FAIL」
- [ ] 「实现未交付」与「需补用例」分开列

### T3 额外检查

- [ ] G2.5 + deploy_url 一致
- [ ] UI：`functional` 条数 = pytest 收集数
- [ ] Apifox 报告路径存在
- [ ] 合并报告逐条 AC 有证据

### T2/T3 输出格式

```text
【测试产物评审】<阶段 T2|T3> <链接或路径>
结论：PASS / FAIL / BLOCKED
阻断项：
- ...
建议项：
- ...
轮次：第 N / 3 轮
```

---

## 边界

- 只评测试产物，不评实现代码
- 不替代 Leader `multica-verification`
- 第 3 轮仍 FAIL → 升级人类
- **即使**用户对本 Agent 说「导入 JIRA」，也**禁止**执行 import
