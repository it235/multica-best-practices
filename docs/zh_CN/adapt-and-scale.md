# 裁剪与扩展

> 先跑起来，再调整。不要把第一天花在「设计完美配置」上。

## 什么时候用 Squad，什么时候直接派给 Agent

| 场景 | 做法 |
| --- | --- |
| 单步小任务（改 typo、加一行配置） | 直接派给一个 Agent，不需要 Squad |
| 多阶段任务（设计 → 实现 → 审查 → 测试） | 用 Squad + Starter |
| 紧急生产故障 | bug-fix Starter |
| 研究 / 技术调研 | 参考 technical-research（见下文） |

原则：**单 Agent 能做的，不要上 Squad。** Squad 的价值是跨阶段协调，不是越多越好。

## 从最小组合开始

不是所有任务都需要 4 个 Worker。常见的成长路径：

```text
1 Agent   → 直接派活
2 Agents  → Frontend/BackendDev + Reviewer（实现 + 独立业务评审）
3 Agents  → Leader + Frontend/BackendDev + Reviewer（有人判门 + 评审）
4 Agents  → Leader + Architect + Frontend/BackendDev + Reviewer（有设计环节）
5 Agents  → 完整 Starter（+ Tester）
6+ Agents → 前后端同场（FrontendDev + BackendDev 并行）
```

每加一个 Agent，都要问：**新增的独立判断点，值不值得额外的上下文损耗？**

## 什么时候需要更严的流程

以下场景升级为严格交付流程（逐阶段门禁、证据留档、人工审批）：

- 涉及生产数据 / 线上发布
- 涉及安全
- 多模块、多团队协作
- 无法自动验证正确性的领域

反之，探索型 / 低风险任务应使用轻量流程。

## 模型适配

不同模型的能力差异明显：

- 强推理模型：可以承担 Leader 判门与 Reviewer 业务评审这类角色，门禁可以更严。
- 弱模型：缩小每个 Agent 的任务粒度，把步骤写得更明确，必要时增加人类检查点。

先按默认 Starter 跑一个真实任务，再根据失败模式调整，而不是提前为「万一」做准备。

## 用 AI 帮你适配仓库到你的技术栈

如果你不想手工改模板，可以直接复制下面这段到 Multica 或任意 AI：

```text
你是本仓库（multica-best-practices）的适配助手。
请把 templates/zh_CN/squad/software-development 这套模板适配到我的技术栈（
[填入语言 / 框架 / 工具链]），要求：
1. 验证命令替换成我们项目的真实命令（lint / test / build）。
2. 保留 G0–G4 门禁结构，只改验证方式和示例。
3. 不新增角色，不扩大流程。
4. 输出可以直接粘贴到 Multica 的完整配置。
```

## 试点推广清单

从 0 到团队推广时：

1. **先跑一个真实项目**：选一个低风险、边界清晰的 Issue，完整跑完 software-development Starter。
2. **复盘**：记录门禁结论与失败模式，调整模板，而不是一上来就扩流程。
3. **再推广**：稳定后再引入其他 Starter 或新增 Agent。

## 常见问题（FAQ）

**Q：Starter 里没有 PM / QA，够用吗？前端 / 后端呢？**

A：普通功能六个角色已足够。PM 职责可以用 Issue 模板替代（背景 / 目标 / 非目标），QA 职责由 multica-verification skill 判门 + Tester + CI 承担。前端 / 后端已经拆分为 FrontendDev / BackendDev（前端要对接 UI 设计，后端不接触 UI），且**按 Issue 的「涉及端」范围路由，任意角色可缺失**——无设计 / 无前端 / 无后端都是同一套 Squad 指令的排列组合。

**Q：我可以用自己的 Squad 流程吗？**

A：可以。Starter 的核心价值是「职责边界」和「证据门禁」，流程本身应该随你的项目调整。多实例复用见 [`naming-conventions.md`](./naming-conventions.md)（角色+项目+成员标识）。

**Q：为什么没有 technical-research Starter？**

A：研究类任务的最小组合是「Researcher → Leader 判门（multica-verification skill）→ Human」，等有真实需求再补，避免未经实战验证的模板（见 [`ROADMAP.md`](../../ROADMAP.md)）。

## 参考

- Multica 官方文档与社区实践链接见 [`README.md`](../../README.md) 底部的「资源」
- 门禁实现：CI 硬门禁模板随 `multica-gate-setup` skill 自包含（[`templates/zh_CN/skills/devops/multica-gate-setup/`](../../templates/zh_CN/skills/devops/multica-gate-setup/)）
