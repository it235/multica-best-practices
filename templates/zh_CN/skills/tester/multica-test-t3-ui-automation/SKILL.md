---
name: multica-test-t3-ui-automation
description: T3 UI 自动化：pytest+Playwright，1 功能用例 = 1 个 e2e 测试；路径读 MULTICA.md §2；在 deploy URL 执行。
version: 1.2.0
---

# Test UI Automation（功能用例 → UI 1:1）

把 **T1 Confluence / T2 入库** 的 Playwright 用例在 **部署环境** 执行。

> T2 应在 **MULTICA.md §2 UI E2E 路径** 编写/积累脚本（见 `docs/test-automation-in-repo.md`）。T3 门禁见 `multica-test-orchestration`。

## Platform 协作

| Platform skill | 本 skill 用途 |
| --- | --- |
| — | 无直接 platform 调用；`page_url` / 用例集来自 Issue 评论与 T1 产物 |

UI 在部署环境执行；环境 URL 由 DevOps / Leader 写入 JIRA 评论（见 `multica-artifact-cicd-sync`）。

## 原则

- **入仓路径**：Read 目标 repo **MULTICA.md §2**（分仓按 Issue 矩阵各读一份）；缺文件 → BLOCKED
- **无 e2e 目录时**：在 MULTICA 指定路径按 `framework-template.md` 初始化（禁止 `/tmp/ui-auto-*`）
- **禁止前置**：`xmind-ui-automation`、`req-figma-ui-automation`、公司 **`playwright.git` 外挂仓库**（与本仓 MULTICA §2 路径不矛盾）
- **1:1**：每条自动化 CASE → 恰好一个 `test_*.py`
- **步骤对齐**：`steps[i]` → 第 i 个操作；`expected_results[i]` → 该步断言（等长）
- **不编造**：locator 来自 **打开 page_url 后**的真实页面；找不到 → **BLOCKED**

## 输入（缺则中断）

```text
repo_root:               # Issue 仓库矩阵；Read MULTICA.md
e2e_dir:                 # MULTICA.md §2 UI E2E 路径（默认 tests/e2e/）
cases_source:            # T1 Confluence 或 e2e_dir 内 test_*.py
page_url / deploy_url:   # Issue 评论
jira_key:
auth_mode:               # none | form_login | sso | cookie
auth_user_env / auth_pass_env:
```

### 账号密码（强制）

- `page_url` **不等于**已登录；需登录系统必须给 `auth_mode` + env 变量名
- **禁止**把账号/密码写进：用例 JSON、脚本、XMind、JIRA 评论、Allure 正文
- 用例前置只写权限语义；真实凭据只放 Agent Secret / gitignore `.env`
- 执行前检查 `auth_user_env`/`auth_pass_env` 非空；为空 → 中断，提示配置 Secret **勿回贴 Issue**
- `auth_mode=none`：仅无需登录页面
- `auth_mode=cookie`：本地 `storage_state` 路径，不把 cookie 贴评论

未确认、无 URL、需登录但 env 空、steps/expected 不等长 → 停止。

## 流程

### Phase A — 确认用例集

1. 只读 `functional`（忽略 `api`）
2. 校验 `len(steps)==len(expected_results)` 且非空
3. 列出 case_id → test 方法对照表（条数 = functional 条数）

### Phase B — 框架（e2e_dir）

若 `{repo_root}/{e2e_dir}/` 无 `pytest.ini`：按 `framework-template.md` 生成于 **该目录**。  
已有本 skill 骨架 → 增量加用例。  
勿在 repo 外另建平行 playwright 工程。

```bash
cd {e2e_dir}   # MULTICA.md §2 UI E2E 路径
python -m venv .venv
.venv/Scripts/pip install -r requirements.txt
.venv/Scripts/playwright install chromium
```

### Phase C — 一对一生成/补全

T2 应已建骨架；T3 补 locator、修断言。规则见 [`references/case-mapping.md`](references/case-mapping.md)。

### Phase D — 执行

```bash
cd {e2e_dir}
.venv/Scripts/pytest . -q --alluredir artifacts/allure-results
```

## 输出

| 产物 | 说明 |
| --- | --- |
| `{e2e_dir}/` 变更 | **commit 到 deploy branch**（FIX 后同样） |
| `artifacts/case_map.md` | case_id ↔ 文件 ↔ 结果 |
| Allure / pytest 日志 | 按条 PASS/FAIL/SKIP(BLOCKED) |
| **Issue 评论** | 映射表 + commit SHA + 失败明细 |

本 skill **不对整单 AC 做 PASS 裁决**；T3 总报告由 `multica-test-orchestration` 合并。

## FAIL / ERROR 分诊

UI 自动化 FAIL 时：**@Tester** 按 `multica-test-orchestration/references/t3-failure-triage.md` 分诊。locator/步骤错 → Tester 修；页面行为不符 AC → 派 FrontendDev。禁止 Frontend 未分诊就改 pytest 降标。

## 禁止

- 使用 `xmind-ui-automation`、`req-figma-ui-automation`、**外部 playwright.git 替代本仓 MULTICA §2 e2e 目录**
- 用例只存在于临时目录、不入 Git
- 一条功能用例拆成多个 test 或多条合成一个
- 把接口请求写进 UI 用例（接口走 Apifox）
- G2.5 前把结果当成 T3 PASS
- 把明文密码写进 Issue 或脚本
