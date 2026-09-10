# Bug Fix Starter

> 最小小队组合：**Bug 修复不需要经过 Architect。**
> 复用 [`../../agents/`](../../agents/) 的 Agents（Leader / FrontendDev / BackendDev / Tester / Reviewer），只换编排。

## 流程

```text
Bug Issue
  ↓ 确定影响面（前端? 后端?）
  ↓
FrontendDev / BackendDev（按影响面）
  复现 → 根因 → 修复 + 回归测试
  ↓
Leader（multica-verification skill）
  独立复跑验证
  ├─ FAIL → 回对应实现者
  └─ PASS ↓
  ↓
Reviewer（业务评审，必要时）
  ↓
Human
  验收 → Done
```

## 阶段分工

| 阶段 | 负责人 | 产出 | 检查人 |
| --- | --- | --- | --- |
| 复现 | Frontend / BackendDev | 可复现步骤 + 根因 | — |
| 修复 | Frontend / BackendDev | 最小范围修复 + 回归测试 | — |
| 验证 | Leader | 独立复跑结论（PASS / FAIL） | Leader（multica-verification skill） |
| 评审 | Reviewer | 业务风险判断（必要时） | Reviewer |
| 验收 | Human | 上线 / Done 决策 | Human |

## 与 software-development 的区别

| 环节 | Software Development | Bug Fix |
| --- | --- | --- |
| 设计 | Architect 先设计 | 跳过，先复现 + 定位根因 |
| 实现 | Frontend / BackendDev（按范围） | Frontend / BackendDev（按影响面） |
| 判门 | Leader 用 multica-verification skill（G1–G3） | Leader 用 multica-verification skill 复跑修复验证 |
| 测试 | Tester 全量验收 | 针对性的回归测试 |
| 验收 | Human | Human |

## 为什么没有 Architect

Bug 的目标是「恢复正确行为」，不是「引入新能力」。多一个设计角色只会拖慢修复、增加上下文损耗。

这正体现了本仓库的核心原则：

> **最佳实践不是固定的五 Agent 流程，而是针对不同任务选择最小的 Agent 组合。**

## 上手

1. 按 [`../../agents/`](../../agents/) 创建 Agents：Leader / FrontendDev / BackendDev / Tester / Reviewer。
2. 复制共享判门 Skill：[`../../skills/leader/multica-verification/SKILL.md`](../../skills/leader/multica-verification/SKILL.md) 挂给 **Leader**（本 Starter 只依赖这一个 Skill）。
3. 把本目录 [`squad.md`](./squad.md) 复制到 Squad Instructions（覆盖默认编排）。
4. 用 [`issue.md`](./issue.md) 创建 Bug Issue。
5. 分配给 Squad。

## 重要提醒

修复类任务尤其容易「为了快速上线而跳过验证」。CI、回归测试、人类审批这些硬约束必须留在工程系统里，不要只靠 Agent 自觉。

## 何时使用

- 生产事故紧急修复
- 功能行为不符合预期
- 回归问题

## 何时不用

- 新功能开发（用 software-development）
- 大型架构迁移
