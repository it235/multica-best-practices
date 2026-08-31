# Software Development Starter

> 开箱即用的 Multica 小队，用于常规软件功能开发。
> **复制 → 粘贴 → 运行**，5 分钟起步。

## 团队

```text
                Leader
                  │
    ┌─────────────┼─────────────┐
    ↓             ↓             ↓
Architect  FrontendDev  BackendDev
    │             │             │
    └──────┬──────┴──────┬──────┘
           ↓             ↓
        Tester（用例左移）   ↓
        Reviewer（业务评审）
```

## 工作流

按 Issue 范围裁剪，任意角色可缺失：

```text
Issue
  ↓ G0 确定范围（设计? 前端? 后端?）── 范围含糊 → 回写 Issue / 问人类
  ↓
[设计] Architect ── G1：Leader(multica-verification skill) 对齐验收标准 + Reviewer 业务评审 ── FAIL → 回 Architect
  ↓ PASS
[并行]
  ├─ [后端] BackendDev：API 契约 → Leader 判门
  └─ [测试] Tester：功能用例 → Leader 判门
  ↓ G1.5：范围内分支全部通过
[实现与接口用例]（API 契约就绪后并行）
  ├─ [前端] FrontendDev（对接 UI 设计）→ G2：Leader 复跑验证命令
  ├─ [后端] BackendDev → G2：Leader 复跑验证命令
  └─ [测试] Tester：接口测试用例 → Leader 判门
  ↓ G2：范围内分支全部通过
[测试] Tester：执行 → 测试报告
  ↓ G3：Leader 复核是否逐条覆盖验收标准 ── FAIL → 回对应实现者
  ↓ PASS
Human（G4 人类验收）
  ↓
Done
```

> `[xxx]` = 范围包含该角色才执行；缺失的角色直接跳过对应行，门禁链不断。

## 产物与门禁

| 产物 | 产出者（按范围） | 门禁 |
| --- | --- | --- |
| 需求就绪 | Issue / 人类 | G0（范围 + 目标 + 验收标准） |
| 设计 | Architect | G1（Leader 用 multica-verification skill + Reviewer 业务评审） |
| API 契约 | BackendDev | Leader 判门（前端 / 测试的并行输入） |
| 功能用例 | Tester | Leader 判门 |
| 开发就绪 | Leader | G1.5（范围内 API 契约 / 功能用例均通过） |
| 前端实现 | FrontendDev | G2（Leader 复跑验证命令） |
| 后端实现 | BackendDev | G2（Leader 复跑验证命令） |
| 接口测试用例 | Tester | Leader 判门 |
| 测试报告 | Tester | G3（Leader 复核逐条对照） |
| 验收 | Human | G4（交付决策） |

## 单任务执行契约

Leader 每次派活只派一个可独立验收的产物，并明确五项：任务、带版本的输入、输出格式、验证与 PASS 条件、修改边界。成员必须按「结论 / 产物或变更 / AC 对照 / 验证证据 / 风险与待确认项」回执；只报“完成”不算交付。主流程状态与并行分支状态由 Leader 统一维护，汇合门禁未通过不得推进。

## 何时使用

- 新功能 / 小到中型改动
- API、后端、前端开发（前后端可拆分，按 Issue 范围路由）
- 需求清晰的重构

## 何时不用

- 生产事故紧急修复 → 用 [`bug-fix`](../bug-fix) Starter
- 大型架构迁移
- 高度模糊的产品探索

## 5 分钟上手

### Step 1 — 创建 Agents

在 Multica 创建 Agent（按你的范围决定建哪些；命名遵循 [`docs/naming-conventions.md`](../../../../docs/zh_CN/naming-conventions.md) 的「角色+项目+成员标识」）。最小可用集合：

```text
Architect
FrontendDev
BackendDev
Tester
Reviewer
```

范围含 CI/CD 时再加 `DevOps`；`ProductManager` 在 Issue 未给出就绪范围时启用。把 [`../../agents/`](../../agents/) 下对应文件的代码块分别复制到各 Agent 的 Instructions。

> Leader 不需要单独建 Agent：`squad.md` 就是 Leader 的行为配置（Multica 的 Squad Instructions 只注入 Leader）。

### Step 2 — 创建 Skills

在 Multica 创建 16 个 Skill：

| Skill | 来源 | 挂给谁 |
| --- | --- | --- |
| `multica-verification`（判门，必备） | [`../../skills/multica-verification/SKILL.md`](../../skills/multica-verification/SKILL.md) | **Leader** |
| `multica-gate-setup` | [`../../skills/multica-gate-setup/SKILL.md`](../../skills/multica-gate-setup/SKILL.md) | Leader（集成 CI 硬门禁时） |
| `multica-test-design` | [`../../skills/multica-test-design/SKILL.md`](../../skills/multica-test-design/SKILL.md) | Tester |
| `multica-requirement-analysis` | [`../../skills/multica-requirement-analysis/SKILL.md`](../../skills/multica-requirement-analysis/SKILL.md) | Leader / Architect |
| `multica-technical-design` | [`../../skills/multica-technical-design/SKILL.md`](../../skills/multica-technical-design/SKILL.md) | Architect |
| `multica-implementation` | [`../../skills/multica-implementation/SKILL.md`](../../skills/multica-implementation/SKILL.md) | FrontendDev / BackendDev |
| `multica-artifact-req-sync` | [`../../skills/multica-artifact-req-sync/SKILL.md`](../../skills/multica-artifact-req-sync/SKILL.md) | ProductManager |
| `multica-artifact-ui-sync` | [`../../skills/multica-artifact-ui-sync/SKILL.md`](../../skills/multica-artifact-ui-sync/SKILL.md) | Designer |
| `multica-artifact-design-sync` | [`../../skills/multica-artifact-design-sync/SKILL.md`](../../skills/multica-artifact-design-sync/SKILL.md) | Architect |
| `multica-artifact-api-sync` | [`../../skills/multica-artifact-api-sync/SKILL.md`](../../skills/multica-artifact-api-sync/SKILL.md) | BackendDev |
| `multica-artifact-test-sync` | [`../../skills/multica-artifact-test-sync/SKILL.md`](../../skills/multica-artifact-test-sync/SKILL.md) | Tester |
| `multica-artifact-cicd-sync` | [`../../skills/multica-artifact-cicd-sync/SKILL.md`](../../skills/multica-artifact-cicd-sync/SKILL.md) | DevOps |
| `multica-test-automation` | [`../../skills/multica-test-automation/SKILL.md`](../../skills/multica-test-automation/SKILL.md) | Tester（T3） |
| `multica-platform-jenkins` | [`../../skills/multica-platform-jenkins/SKILL.md`](../../skills/multica-platform-jenkins/SKILL.md) | 平台层占位壳（CI/CD） |
| `multica-platform-jira` | [`../../skills/multica-platform-jira/SKILL.md`](../../skills/multica-platform-jira/SKILL.md) | 平台层占位壳（Issue） |
| `multica-platform-confluence` | [`../../skills/multica-platform-confluence/SKILL.md`](../../skills/multica-platform-confluence/SKILL.md) | 平台层占位壳（Wiki） |

> 16 个 Skill 全部共享放在 [`../../skills/`](../../skills/)，统一 `multica-` 前缀命名空间，分三类：判门/设计类、产物编排类（`multica-artifact-*-sync`）、平台层占位壳（唯一允许出现内网地址/凭据的地方，公开仓库只给占位壳）。Skill 靠**名称**挂载，谁需要就在自己的 Instructions 里写「用 xxx skill」，与仓库路径无关。

### Step 3 — 创建 Squad

创建一个 Squad，把 [`squad.md`](./squad.md) 的代码块复制到 Squad Instructions。

### Step 4 — 创建 Issue

把 [`issue.md`](./issue.md) 的模板复制到新 Issue，填上你的需求。

### Step 5 — 分配

把 Issue 分配给这个 Squad。

### Step 6 — 运行

小队会自动按上面的「工作流」走完：

```text
Issue → [设计] → [并行产物] → [实现] → [测试] → Human
```

每个产物的门禁由 Leader 用 multica-verification skill 判门，PASS 才放行；范围里没有的角色直接跳过。
就这些。先跑一个真实需求，再按你的团队调整。

## 重要提醒

这个流程是**协调指引**，不是硬性约束。它不能替代：

- CI 硬门禁（见 [`../../skills/multica-gate-setup/`](../../skills/multica-gate-setup/)）
- 分支保护 / PR Review
- 人类审批

multica-verification skill 是 Agent 世界的**软门禁**（由 Leader 执行判门），「必须通过」的硬约束请放在工程系统里强制执行，不要只依赖「Agent 被要求这样做」。

## 目录

| 文件 | 用途 |
| --- | --- |
| `squad.md` | Squad Instructions（条件路由 + 产物门禁 + 证据要求） |
| `issue.md` | 标准 Issue 模板（精简为需求契约：来源二选一 + 背景/目标/范围含涉及端/非目标/验收标准，仅此） |
| `README.md` | 本文件（工作流 + 产物门禁 + 上手步骤） |
| [`../../agents/`](../../agents/) | 共享 Agent Instructions（architect / frontend-developer / backend-developer / tester / reviewer / devops / leader） |
| [`../../skills/`](../../skills/) | 共享 Skill（统一 multica- 前缀：判门 / 集成 CI / 测试设计 / 需求分析 / 技术设计 / 实现 / 产物落地 / 平台层占位壳） |

## 为什么有效

这个 Starter 有 9 个角色：Leader 负责编排与判门，ProductManager（产品需求 / PRD）把想法变可评审交付物，Architect（技术架构）/ Designer（UI）/ FrontendDev / BackendDev / Tester（T1/T2/T3 三阶段）/ DevOps（G2.5 触发 CI/CD）各管一段产物，**Reviewer 做业务评审**。
判门动作标准化为 [`../../skills/multica-verification/SKILL.md`](../../skills/multica-verification/SKILL.md)，由不产出的 Leader 执行（执行者与判门者不同源）；客观验证能机器化就升级到 CI 硬门禁（见 [`../../skills/multica-gate-setup/`](../../skills/multica-gate-setup/)）。
**门禁锚定产物而不是角色**：Issue 的「涉及端」决定路由，缺失角色对应产物跳过、门禁链不断——无设计 / 无前端 / 无后端 / 全栈都是同一套指令的排列组合。
路由逻辑只写一次（Squad），不复制进每个 Agent；每个 Agent 职责很窄，可以原样照搬。

## 常见失败

- 给每个 Agent 都塞一遍完整流程 → 冗余且互相矛盾。
- 让产出者自己判自己「通过」→ 作者会本能地为自己找理由，等于没查。
- 需求没写验收标准 / 没勾「涉及端」就开工 → 小队会卡在 G0，等于白跑。
