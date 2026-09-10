# 门禁与证据

多 Agent 协作最常见的翻车点：**Agent 说「做完了」，但没人知道是不是真的。**

解决方式只有一套：**每个阶段设门禁，每个门禁要求证据，关键证据由非产出者复跑。**

## 门禁是什么

门禁 = 一个可以明确回答「过 / 不过」的检查点。在 software-development Starter 中是 G0–G4：

| 门禁 | 内容 | 谁来判 |
| --- | --- | --- |
| G0 | 需求就绪：有目标 + 可测试的验收标准 | Leader / Human |
| G1 | 设计通过：设计与验收标准对齐 + 业务上可接受 | Leader（multica-verification skill）+ Reviewer（仅 software-development 默认在 G1 做业务评审；reviewed 版为每产物配专属 Reviewer） |
| G2.5 | CI/CD 部署：G2 PASS 且代码已 push 后，构建部署到测试环境并回传环境 URL | Leader（核对 CI 证据，由 @DevOps 触发） |
| G3 | 测试通过：T3 自动化报告逐条对照验收标准（依赖 G2.5 部署环境） | Leader（复核报告） |
| G4 | 人类验收：交付决策 | Human |

门禁的关键是**可判定**：每个门禁对应一个可以 PASS / FAIL 的问题。判不了，就不是门禁，是愿望。

## 判门动作：multica-verification skill

验证是一个**功能**，不是一个角色。它被标准化为 `templates/zh_CN/skills/leader/multica-verification/SKILL.md`，由 **Leader** 在门禁点（G1 / G2 / G3）触发执行：

- Leader 不产出任何产物 → 判门者与被判门者不同源
- 判门 = 复跑验证命令 + 逐条对照验收标准，不引用产出者的描述；仓库已配置 CI 时**优先引用 CI 结论**（如 `[G2 PASS · CI #123]`），不重复跑（感知做法见 `multica-artifact-cicd-sync` skill）
- 产出者自证（自己跑一遍）不算数，关键命令必须复跑

## 验证与评审是两类检查

| | Verification（验证） | Review（评审） |
| --- | --- | --- |
| 问的问题 | 产物合格吗？有证据吗？ | 方案 / 改动业务上可接受吗？ |
| 判定方式 | 客观可判定：命令输出、逐条对照 | 主观判断：业务意图、风险、可维护性 |
| 执行者 | Leader（multica-verification skill）/ CI | Reviewer（独立角色）/ Human |

验证能标准化成 Skill、能机器化；评审必须由独立的人带着业务视角做。

## 两层门禁：通用门禁 + 专业产出物评审

`software-development` 只有**一层通用门禁**（Leader 用 multica-verification skill 在 G1/G2/G3 复跑）。`software-development-reviewed` 在此基础上叠加**第二层：专业产出物评审**，形成「通用门禁 + 专业评审」两层，且两者标准不同、触发方不同、互不可替代。

### 为什么需要两层

通用门禁回答「**对不对**」：产物是否满足验收标准、流程是否走完——这是流程层保证，不评价专业深度。但光靠它不够：一个「满足了 AC」的前端实现，单测可能全是无效的；一个「通过了验收」的测试报告，覆盖率可能覆盖了低风险路径却漏了关键分支。这些**专业质量问题**需要对应领域的独立评审者来判断。

专业产出物评审回答「**专不专业**」：结合需求、上游产物与资料，对产物本身做专业分析（设计是否合理、单测是否充分、用例/覆盖率是否到位）。

### 两层怎么走（固定顺序）

```text
产出角色完成产物
  → 第 1 层 通用门禁（Leader 触发）：multica-verification skill 复跑验收标准/流程（只管对不对）
  → 若 PASS：
      第 2 层 专业评审（专属 Reviewer 触发）：用 multica-review-* skill 做专业分析（只管专不专业）
        → 若 PASS：产物放行，推进下一阶段
        → 若 FAIL：专属 Reviewer 输出结论 + 修改清单，汇报 Leader
             → Leader 指派对应产出角色修改
             → 修改完再派同一专属 Reviewer 复审（同一人，保证口径一致）
             → 最多 3 轮；第 3 轮仍不通过 → 升级人类判定
  → 若 FAIL：退回作者，按通用门禁 FAIL 计数（连续 3 次升级人类）
```

两层**任一 FAIL 都退回**；专业评审轮次与通用门禁 FAIL 轮次**独立计数，但共用「3 次上限」阈值**——任一层达到 3 次未过即升级人类。

### 角色与专属 Reviewer 映射（reviewed 版）

| 产出角色 | 专属 Reviewer | 评审 Skill | 评审关注点 |
| --- | --- | --- | --- |
| @ProductManager（PRD） | @ProductReviewer | multica-review-product | 范围/目标/验收标准是否清晰可测、是否遗漏关键约束 |
| @Architect（设计） | @ArchReviewer | multica-review-architect | 架构合理性、扩展性、与验收对齐、技术风险 |
| @Designer（UI） | @DesignReviewer | multica-review-designer | 交互合理性、可访问性、与设计系统/验收一致 |
| @FrontendDev（前端实现） | @FrontendReviewer | multica-review-frontend | 与 UI/API 契约吻合度、组件质量、单测是否合理充分 |
| @BackendDev（后端实现 + API 契约） | @BackendReviewer | multica-review-backend | 契约质量、与设计吻合度、错误处理、单测是否合理充分 |
| @Tester（用例 / 测试报告） | @TestReviewer | multica-review-test | 用例覆盖深度、覆盖率文档合理性、与验收逐条对应 |

> Leader 与 DevOps **不配**专属 Reviewer：Leader 是编排者（既判门又评审会同源）；DevOps 产出是部署 URL，已由 CI 硬门禁覆盖。其余常规产出角色全覆盖。

### 三条硬约束（与单层门禁一致，且更严格）

1. **专属 Reviewer 不代替作者修改**：只输出结论 + 修改清单，并汇报给 Leader；由 Leader 指派对应产出角色修问题。这把「评审权」与「修改权」分离，且推进权始终在 Leader。
2. **Leader 不得用评审结论替代通用门禁**：两层各管各的——通用门禁永远由 Leader 亲自跑 multica-verification skill，不得因为专属 Reviewer 说 PASS 就跳过复跑。
3. **专属 Reviewer 与产出者不同源**：同一产物复审必须由同一专属 Reviewer 执行，保证评审口径连续；不得让产出者评审自己，也不得让 Leader 既判门又做专业评审。

### 什么时候用 reviewed 版

- 你需要的不只是「流程走完了」，还要「产物本身专业、经得起推敲」。
- 团队对架构设计、UI、需求、前后端实现、测试产物有较高专业把关要求。
- 希望专业评审意见**独立于实现者**，并由 Leader 统一收敛、指派修改、循环复审。

若只想要轻量流程，用默认 `software-development`（仅 Leader 触发 multica-verification 通用门禁即可）。两种 Starter 除多一层评审外，路由 / 阶段门禁 / 证据 / 失败处理 / 升级人类规则完全一致，迁移成本为零。

## 证据是什么

「完成」这个词没有证据价值。有价值的证据：

- 变更文件列表（git diff 摘要）
- 实际执行的命令 + 完整输出
- 与验收标准的逐条对照（每一条 → 对应的测试或检查）
- 测试 / 检查结果
- 已知限制与风险

## 如何防止「作者自证」

规则很简单：**不要让完成工作的人判断自己的工作是否合格。**

- 实现者不给自己发 PASS
- 判门由 Leader 用 multica-verification skill 复跑（或引用 CI 结论），而不是引用实现者的描述
- 自动化验证命令的输出，判门者亲自复跑

## 软门禁（Agent 世界）与硬门禁（CI）

LLM 指令是引导，不是安全边界。**必须被遵守的规则，放在 LLM 之外：**

```text
Tests / Lint / Build / CI / 分支保护 / PR 审批
```

- **软门禁**：Leader 在 Squad 内用 multica-verification skill 判门（G1–G3），靠指令和证据约束，适合起步、无 CI 或探索期。
- **硬门禁**：由 CI 出具、不可伪造的检查（部署模板与做法见 `multica-artifact-cicd-sync` skill：`templates/zh_CN/skills/devops/multica-artifact-cicd-sync/`）。当需要比人工检查更可信的结果时，把关键门禁交给 CI——门禁出具方必须和被门禁方不同源。

软门禁和硬门禁是**同一个验证功能的两种执行环境**：Agent 世界的 Skill 与工程世界的 CI。能上 CI 就上 CI。

不要依赖「Agent 被要求不要这样做」。

## 一条真实需求的完整走查

以「新增导出 CSV 功能」为例：

1. **G0**：Issue 写明验收标准，例如「调用导出接口后，返回的 CSV 包含全部筛选结果」。
2. **G1**：Architect 给出最小改动方案（复用现有导出中间件）。Leader 用 multica-verification skill 确认方案覆盖验收标准，Reviewer 评审业务上可接受。
3. **实现**：Frontend / BackendDev（按 Issue 范围）提交代码 + 单元测试 + 变更文件列表 + 验证命令输出（自证）。
4. **G2**：Leader 优先引用 CI 结论（未配 CI 则自己复跑验证命令），并检查 diff 是否只涉及本次需求。PASS。
5. **G2.5**：@DevOps 在 G2 PASS 且代码已 push 后触发 CI/CD，构建部署到测试环境并回传环境 URL；Leader 核对 CI 证据判 G2.5 PASS。（无 @DevOps / 无 CI 时可略过，T3 退化为本地或手动验证并显式标注。）
6. **G3**：Tester 按 multica-test-t1-design skill 出功能 / 接口用例；在 G2.5 部署环境就绪后，用 multica-test-t3-ui-automation 执行，按验收标准验证「筛选 → 导出 → 检查 CSV 内容」出测试报告，Leader 复核报告是否逐条覆盖验收标准。
7. **G4**：人类查看证据后决定是否合并 / 上线。

任何一个 G2/G3 FAIL，任务回到对应实现者，且**之前的门禁结论作废，需要重新走**——不能因为「上次通过了」就跳过复跑。更一般地：**任一产物被修改，其下游门禁立即失效，必须重判**。不只是实现改动：设计 / API 契约 / 用例一旦变更，下游的实现、测试、验收门禁同样重新失效，不得沿用旧 PASS。范围内某产物若判定为「不适用（N/A）」，也禁止静默跳过——必须显式标注 N/A、写明理由并由 Leader 确认；未确认的 N/A 视为范围缺失，回写 Issue。

### 门禁结论的取值

判门结论不只有 PASS / FAIL，建议用四值：

- **APPROVED（通过）**：产物成立，开放下游。
- **APPROVED_NA（不适用但通过）**：该产物经确认不在本范围（如「无设计」时设计产物），分支视为已通过、**不产出该产物**，下游按「无该产物」分支走。注意它与普通 APPROVED 的下游差异由 Leader 在路由图里写明，不能混为一谈。
- **REJECTED（驳回）**：退回原作者，必须给出阻断问题、定位证据、责任人与可验证的通过条件；不得用「继续优化」等模糊意见。
- **BLOCKED（阻塞）**：等待缺失信息 / 依赖，不视为通过，不得用「环境问题」直接判过。

### 汇合门禁（并行分支）

当多个产物并行推进、在某一门禁点汇合时（如软件开发的 G2 = API 契约 + 功能用例，G3 = 前端 + 后端 + 接口用例），该门禁必须**全部分支都 APPROVED 才开放下游**；任一分支被 REJECTED 只退回该分支，汇合保持关闭。判门者对每个分支独立给结论，不替未通过分支说情。

### 需求 / 设计类产物的「AI 可读」纪律

需求与产品文档不仅是给人评审的，下游 @Architect / @Designer / @FrontendDev / @BackendDev / @Tester 会用它拆任务。Leader 判 G0/G1 门禁时，除四值外还要检查这些硬约束（源自 Product Manager 角色）：

1. **标题稳定**：同一文档的标题层级、章节名固定，便于 AI 定位（如「验收标准」永远叫 AC-，不今天叫「验收」明天叫「通过标准」）。
2. **表格字段稳定**：字段表 / 指标口径表的列名固定（如「字段名 / 类型 / 必填 / 说明」）。
3. **规则有编号**：业务规则、验收标准、目标一律用 G- / FR- / BR- / AC- / KPI- / OP- / RISK- 编号，禁止无编号散文式要求。
4. **待确认集中**：所有不确定内容只进 OP- 清单，不散落在正文假装已确认；OP- 未关闭不得进开发。
5. **文档互链**：PRD / 原型说明 / 指标口径 / 验收清单互相链接，引用不靠"前文那个表"。
6. **冲突指明准绳**：资料冲突时写明「以哪份文档为准」，不让两份矛盾文档并存无裁决。
7. **禁用模糊词**：禁止「等等 / 相关 / 适当 / 优化一下 / 完善一下」这类无法开发与验收的词；要求必须可测。
8. **规则文字化**：重要规则必须有文字版，不只在图片 / 原型里（图是补充，不是唯一来源）。

> 违反任一条，G0/G1 判 REJECTED 并点名缺哪条，不静默放过。

### 判门者不改产物

判门者（Leader 用 multica-verification 复跑，或独立 Reviewer）只输出结论与修改清单，**不代替作者修改被审产物**；编排者本人也不得代替审核员批准。这保证了「作者不自审」的硬约束在流程层面成立。
