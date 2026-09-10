# 自动化资产生命周期（Apifox + Playwright + Git）

与 `docs/test-automation-in-repo.md` 配套；@Tester 在 T1/T2 开始积累，T3 执行。

---

## 总览

```text
T1  Confluence 用例全文 + Apifox 场景（契约并行）
    ↓ 👤 review + 口令
    XMind → 测试管理平台（可选）
T2  Confluence 增量 + Apifox 补场景 + MULTICA §2 e2e 骨架入库
T3  deploy 环境跑 Apifox CLI + pytest（e2e_dir 来自 MULTICA）→ 修则 commit deploy branch
```

---

## Apifox（接口）

| 时机 | 动作 |
| --- | --- |
| T1 并行 | API 契约发布后：读 `openapi.json` / Confluence 契约 → `multica-platform-apifox` 补场景（**AI 分支**；见 openapi-branch-workflow.md） |
| T2 | 按补充清单追加 endpoint 场景；更新 `tests/api/<ISSUE-KEY>/manifest.json` |
| T3 | `multica-test-t3-api-automation` → `run_apifox.py`；scenarioIds 来自 manifest 或 Issue 评论 |

**禁止**：接口用例 import JIRA；主步骤只在 Apifox。

---

## Playwright（UI）

| 时机 | 动作 |
| --- | --- |
| T1 | 在 Confluence 写清 CASE-ID、步骤、预期（**不写脚本**） |
| T2 | 对 T2 清单中 **必须** 自动化的 CASE：在 `{e2e_dir}/test_{case_id}.py` 建骨架（locator 可 TODO → T3 BLOCKED 若仍缺） |
| T3 | `pytest {e2e_dir}/` 对 deploy_url；FAIL → t3-failure-triage → 修脚本 commit |

框架：沿用 `multica-test-t3-ui-automation/references/framework-template.md`，**目标目录 = MULTICA.md §2 UI E2E 路径**，禁止每次新建临时目录。

---

## Git 合入

- **路径**：各 repo 根目录 **MULTICA.md** §2（分仓读各自 MULTICA）
- **分支**：与 Issue deploy branch 一致；G2 前 commit
- **提交**：e2e 脚本、manifest；不提交 `.env`

---

## Confluence vs XMind（当前策略）

| 阶段 | XMind |
| --- | --- |
| T1/T2 阶段 A | **不生成** |
| 👤 口令后阶段 C | `generate_xmind.py` → `import_to_tracker.py` |

Confluence 为 **审核与协作主副本**；JSON 可为生成/导入的工作文件，不必作为交付物对外宣称。
