# T3 合并报告模板

> 由 `multica-test-orchestration` 在 UI + 接口两侧证据齐（或单侧可跑）后输出。对应 **G3**。

```markdown
# T3 验收测试报告 — {JIRA_KEY}

## 整单结论
**PASS | FAIL | BLOCKED**

> 任一侧 BLOCKED 且该侧 AC 无法他侧替代 → 整单不得 PASS。

## 环境
- G2.5: {PASS | N/A | 未过}
- deploy_url: {url}
- page_url: {url 或同 deploy}

## 通道摘要
| 通道 | 结论 | 证据 |
| --- | --- | --- |
| UI（pytest+Playwright） | PASS/FAIL/BLOCKED/N/A | case_map.md / Allure |
| 接口（Apifox CLI） | PASS/FAIL/BLOCKED/N/A | run_apifox JSON / 日志 |

## AC 逐条裁决
| AC- | 结果 | 证据来源 |
| --- | --- | --- |
| AC-1 | PASS/FAIL/BLOCKED | UI-xxx / Apifox-xxx / 人工附录* |

*人工附录：仅 Leader 书面授权；标题须「非自动化、不替代 G2.5」；**不得**因此把整单自动化判 PASS。

## FAIL 明细（如有）
- AC-x：复现 / 期望 / 实际 / 严重度 / 证据路径

## BLOCKED / 范围外（如有）
- …

## 附件
- UI: …
- Apifox: …
```

## 分流Reminder

| 情况 | 行为 |
| --- | --- |
| 仅 UI 材料齐 | 只跑 UI；Apifox 三 ID 标 N/A 不算缺失 |
| 仅接口材料齐 | 只跑 Apifox |
| 都齐 | 都跑后合并 |
| 一侧缺材料 | 该侧中断；另一侧可跑；整单不得 PASS |
| G2.5 N/A 且无 deploy_url | 两侧自动化 BLOCKED |
| G2.5 N/A 但有 deploy_url + Leader 书面允跑 | 可跑；报告注明 G2.5 降级 |

## 人工附录（Leader 授权时）

- 可列手工步骤结果，标题 **「非自动化、不替代 G2.5」**
- 整单自动化结论仍为 **BLOCKED**，除非所有 AC 已在部署环境被充分验证（Leader 书面确认）
