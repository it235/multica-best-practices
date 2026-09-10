# T1 用例导入契约（import_to_tracker.py）

> 本 skill **不随附**批量导入脚本——它强绑定具体测试管理平台（Jira 用例插件 / TestRail / Zephyr / 自研平台…），无法通用化。
> 团队按所用平台自行实现 `import_to_tracker.py`，**满足以下契约与硬约束**即可与 T1 流程无缝衔接。

## 接口约定

| 参数 | 含义 | 约束 |
| --- | --- | --- |
| `--jira-url` | 目标需求 Issue 完整 URL | 必填 |
| `--input` | `test_cases.json`（T1 结构化用例，见 `output-format.md`） | 必填；**仅功能用例** |
| `--suite-name` | 测试集名称 | **必填且唯一**，命名规则见 `generation-workflow.md` |
| `--dry-run` | 预览，不实际写入 | 可选 |
| `--manual` | 逐条确认 | 可选 |
| `--update-existing` | 更新已存在用例描述 | 可选 |

可选输出：返回用例集 URL，由 Tester 回写 Issue（Relates）+ 更新 Confluence 状态「已导入 JIRA」。

## 硬约束（与 T1 流程一致）

1. **人类口令后才运行**：仅当收到明确导入指令（如「审核通过，导入 JIRA」）才执行；阶段 A 发布 Confluence 后**不**同轮跳过审核或生成 XMind。
2. **每批只导入一次**、只归入**一个**测试集；禁止重复执行、禁止二次关联脚本。
3. **接口用例永不导入**（接口走 Apifox + manifest）。
4. **Relates 闭环**：需求(Story) ↔ 用例集(Task) 仅 Relates；用例不建 Include 铺开；需求面板挂用例集 Task 而非 Story。
5. **导入前前置校验**：确认 JIRA Key、确认尚未导入、确认 `--suite-name` 唯一、确认名称与需求严格对应。
6. **导入后关联校验**：按上述 Relates 规则自检（参考现网样例）。

## 失败处理

- 已导入过：不要再次导入，直接报告已有用例信息。
- 任一校验失败：停止并报告 BLOCKED，不臆造。
