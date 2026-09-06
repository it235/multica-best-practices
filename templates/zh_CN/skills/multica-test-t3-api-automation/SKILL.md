---
name: multica-test-t3-api-automation
description: Tester T3 接口自动化：G2.5 后 Apifox CLI 跑批 + AC 裁决报告。整合 software-development；CLI 在 multica-platform-apifox。
metadata:
  orchestrates:
    - multica-platform-apifox
  credentials:
    priority:
      - APIFOX_ACCESS_TOKEN
---

# Test Automation（Apifox CLI · T3 接口）

G2.5 PASS 且具备 **部署环境 URL** 后才能跑。场景写入用 `multica-platform-apifox`；本 skill **跑批 + 接口侧 AC 证据**，整单 PASS/FAIL/BLOCKED 由 `multica-test-orchestration` 合并（含 UI 通道时）。

> 整合自 `software-development`。

## Platform 协作

| Platform skill | 本 skill 用途 |
| --- | --- |
| `multica-platform-apifox` | T3 `run_apifox.py` 跑批 + 环境变量注入 |

凭据：`APIFOX_ACCESS_TOKEN`（见 platform-apifox SKILL）。本 skill 不重复 REST/CLI 细节。

## 从评论拼接（先于跑批）

只使用本 Issue 描述 + 全部评论（规则见 `multica-test-orchestration`）。不能拼 → **中断**，禁止 CLI。

| 字段 | 评论齐套条件 |
| --- | --- |
| `g25_pass` | 明确 G2.5 PASS。仅「G2.5 N/A」→ 缺 deploy 证据（除非同时有 deploy_url 且 Leader 书面允跑） |
| `deploy_url` | 评论中的 http(s) 环境地址。无则 BLOCKED |
| `apifox_*` | 有接口自动化：项目 ID + 环境 ID + 场景 ID。契约 N/A → 三字段填 N/A |

## 门禁

| 条件 | 动作 |
| --- | --- |
| `g25_pass` 非 true | **BLOCKED**（G2.5 N/A 同等；除非 deploy_url + Leader 书面允跑） |
| 无 `deploy_url` | **BLOCKED** |
| 用 localhost / mock 冒充部署环境 | **禁止** |

**禁止**因编译/单测/实现者口头通过而 PASS。**禁止**把 BLOCKED 改判 PASS。

## CLI 执行

```bash
pip install -r multica-platform-apifox/scripts/requirements.txt
npm install -g apifox-cli
set APIFOX_ACCESS_TOKEN=<token>

python multica-platform-apifox/scripts/run_apifox.py \
  --issue PROJ-2466 \
  --base-url "<deploy_url from comment>" \
  --json
```

> CLI **唯一入口**：`multica-platform-apifox/scripts/run_apifox.py`（勿使用本 skill 目录下的副本）。

`deploy_url` 注入 Apifox 环境变量；scenario / environment 见 `multica-platform-apifox/config.yaml`。

## 裁决（G3 测试报告 · 接口通道）

对照 Issue **AC-** 逐条，结合 CLI 结果：

| 结论 | 条件 |
| --- | --- |
| **PASS** | 全部 AC 满足且部署环境证据充分 |
| **FAIL** | 有 AC 未满足 + 复现/期望/实际/证据/严重度 |
| **BLOCKED** | 缺环境/G2.5 未 PASS/CLI 无法验证 |

条件用例（T2 标范围外）：记 BLOCKED（范围外），**不得记 FAIL**。

## FAIL / ERROR 分诊（强制）

自动化失败时 **先分诊、再派活**，见 `multica-test-orchestration/references/t3-failure-triage.md`：

| 结论 | 负责人 |
| --- | --- |
| 用例/脚本/断言问题 | **@Tester** 修订并重跑 |
| 产品不符合 AC | **@FrontendDev / @BackendDev**（Tester 派活 + 证据） |
| 环境/部署 | **BLOCKED** → Leader / DevOps |

**禁止**实现者未等分诊就改测试「刷绿」；**禁止** Tester 跳过分诊直接关单。

### 人工附录（Leader 书面授权时）

可列手工步骤结果，标题 **「非自动化、不替代 G2.5」**。整单自动化结论仍为 BLOCKED，除非所有 AC 已在部署环境被充分验证。

## 输出模板

```markdown
# T3 测试报告（接口通道）— {JIRA_KEY}

## 结论
**PASS | FAIL | BLOCKED**

## 环境
- G2.5 / deploy_url / Apifox 运行 ID

## AC 逐条
| AC- | 结果 | 证据 |
|-----|------|------|

## FAIL 明细（如有）
- …

## 自动化日志
- 路径或附件
```

跑批完成后由 `multica-test-orchestration` 合并 UI/接口证据并做整单 AC 裁决（报告链接进 JIRA 为团队可选项）。

## 为什么有效

接口 T3 与 UI T3 分 skill，编排层统一裁决，避免 Apifox 补场景被误当成验收通过。
