# 前端 Review 执行流程

FrontendReviewer 接到 Leader 派活后按本顺序执行。细节勾选项见 [`checklist.md`](checklist.md)。

## 1. 锁定材料

- 读 Multica Issue、最新评论、@FrontendDev 完成说明与附件
- 读 Leader 显式给出的：impl-spec（Confluence）、UI 链接、API 契约、AC-
- 确认**项目仓库**路径与 diff 范围（Multica task workdir 仅临时上下文，不作审查根目录）

## 2. 校验范围

- 对照变更文件列表与实际 diff，确认与 issue 目标一致
- 若项目有 README / `.cursor/rules` / 内部前端规范，加载为审查基准

## 3. 对照审查

- 按 checklist 逐项检查（UI 流程、状态、契约、类型、模式、影响面、测试）
- 必要时运行 lint / 单测 / 类型检查；不能运行时记录原因

## 4. 分级与结论

- 问题归入 Must Fix / Suggest / Nit
- 有 Must Fix → **FAIL**；无 Must Fix 且审查完整 → **PASS**（可带 Suggest/Nit）
- 触发 BLOCKED 条件 → **BLOCKED**，不强行 PASS/FAIL

## 5. 输出并汇报 Leader

- 使用 SKILL.md 输出模板
- 不自行 @FrontendDev 改代码；由 Leader 指派

## BLOCKED（先停再判）

遇以下情况输出 **BLOCKED**，列出缺失项，**不计入** 3 轮 FAIL：

| 条件 | 说明 |
| --- | --- |
| 找不到声称的变更 | diff / 文件列表与完成说明不一致 |
| diff 与 issue 目标明显不匹配 | 改动范围偏离 AC 或 impl-spec |
| 上游描述冲突 | JIRA / Confluence / Issue 口径矛盾，影响判断 |
| AC 或验收标准不清 | 无法客观判断实现是否正确 |
| 缺少必要上下文或权限 | 无法读仓库、契约、UI |
| 改动过大 | 单次 review 无法可靠覆盖，需 Leader 拆 scope |

BLOCKED 与 FAIL 区别：FAIL = 材料足够且存在 Must Fix；BLOCKED = **还未能开始或完成可靠审查**。

## 复审

1. 读上一轮 Must Fix 清单
2. 逐条核对是否已解决
3. 未解决项继续 Must Fix；引入新问题按分级追加
4. 轮次 +1（仅 FAIL 复审计轮；BLOCKED 后补材料重审不计上一轮 FAIL）
