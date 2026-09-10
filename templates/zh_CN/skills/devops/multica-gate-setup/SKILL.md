---
name: multica-gate-setup
description: 集成 CI 硬门禁到目标仓库，并让判门感知 CI 结论。用于部署门禁、读取 check-runs 判 G2、无 CI 时降级软门禁。
---

# Gate Setup（CI 门禁集成）

## 这是什么

把「验证」从 Agent 自觉升级为 CI 机器执行的集成 Skill。
核心思想（`multica-gatekit`）：**门禁出具方必须和被门禁方不同源**——作者无法自己盖章「测试通过」，只有 CI 的真实运行结果才算数。

本 Skill 回答两个问题：

1. **怎么把 gates 装进一个仓库？**（一次性部署）
2. **判门时怎么感知 CI 结论？**（每次任务的 G2）

## 携带的模板文件

部署所需的 3 个模板文件与本 SKILL.md 同目录（Skill 自包含，随 skill 一起复制）：

| 文件 | 作用 |
| --- | --- |
| `delivery-gate.yml` | CI 工作流：在 PR 上跑 lint + test + build，并写入结构化门禁结论 |
| `branch-protection.json` | 分支保护规则：要求 `delivery-gate` 状态检查通过 + 独立审批后才能合入 |
| `apply-branch-protection.sh` | 用 `gh` CLI 把保护规则应用到仓库（修改占位符后运行） |

适用场景：已有可跑的 test / lint / build 命令；不希望「Worker 自证完成」留下作弊空间；多 Squad 并行需要统一合入门禁。

## 能力前提（按环境路由）

Leader 只有 Skill + MCP，无 shell。因此按运行时环境走分支：

| 能力 | 判门（G2） | 部署（一次性） |
| --- | --- | --- |
| 有 GitHub MCP（读） | **真集成**：查 check-runs 读 CI 结论 | — |
| 有 GitHub MCP（写） | — | **真集成**：创建 workflow + 设分支保护 |
| 无 MCP | **弱集成**：读 PR 评论里人类搬运的 CI 结论 | 人类跑脚本，你核对输出 |

## 部署流程（一次性）

1. 读本 Skill 同目录的 3 个模板文件：`delivery-gate.yml` / `branch-protection.json` / `apply-branch-protection.sh`。
2. 按目标仓库替换占位符：

| 文件 | 占位符 | 替换为 |
| --- | --- | --- |
| `delivery-gate.yml` | `pnpm install --frozen-lockfile` | 仓库真实安装命令 |
| | `pnpm lint` / `pnpm test` / `pnpm build` | 仓库真实验证命令 |
| `branch-protection.json` | `"delivery-gate"`（context） | 保持（除非改了 workflow job 名） |
| | `required_approving_review_count` | 独立审批人数（默认 1） |
| `apply-branch-protection.sh` | `YOUR_OWNER` | GitHub 组织 / 用户名 |
| | `YOUR_REPO` | 仓库名 |

> 该分支保护 API 只能要求审批数量，不能用团队 slug 限定“必须由某团队审批”。如需团队级审批，请配置 `CODEOWNERS` 并启用 code owner review，或使用 GitHub Rulesets；本模板不自动创建这些仓库策略。

3. 安装到目标仓库：
   - **有写权限 MCP**：创建 `.github/workflows/delivery-gate.yml`；用 GitHub API `PUT /repos/{owner}/{repo}/branches/main/protection` 设置分支保护（等效于脚本动作，body 用 `branch-protection.json`）。
   - **无 MCP**：给人类明确操作清单——复制 `delivery-gate.yml` 到 `.github/workflows/`；修改两个文件的占位符；`gh auth login` 且有 admin 权限后运行 `bash apply-branch-protection.sh`。
4. 验证生效：查分支保护规则 `GET /repos/{owner}/{repo}/branches/main/protection`，确认 `required_status_checks.contexts` 含 `delivery-gate`；或让人类贴脚本输出。

## 判门流程（G2，每次任务）

1. 通过 GitHub MCP 查 PR 的 check-runs：`GET /repos/{owner}/{repo}/commits/{sha}/check-runs`。
2. 找到名为 `delivery-gate` 的 check 结论（success → PASS，失败 → FAIL）。
3. G2 判定：
   - **CI 存在** → 引用结论（如 `[G2 PASS · CI #123]`），再核对 diff 范围是否只涉及本次需求 → 给 PASS / FAIL。**不重复跑** CI 已覆盖的命令。
   - **CI 缺失** → 降级为软门禁：用 `multica-verification` skill 复跑验证命令。
   - **读不到 CI** → BLOCKED，如实报告，绝不转 PASS。
4. 复跑动作在 CI 存在时是「核对结论 + diff」，不是重跑命令。

## Result

**PASS** —— CI 绿（或复跑通过）+ diff 范围正确。

**FAIL** —— CI 红或 diff 越界。必须给出：问题、为什么重要、位置、修复方向。

**BLOCKED** —— 缺 MCP / 缺 CI / 缺信息，无法验证。如实报告，绝不转成 PASS。

## 与 multica-verification skill 的关系

同一验证功能的两种执行环境：

- `multica-verification`：软门禁，Leader 复跑（CI 缺失时本 Skill 降级回它）
- `multica-gate-setup`：硬门禁集成——部署 + 判门感知 CI 结论

**能上 CI 就上 CI**，软门禁是过渡；两者互补，不冲突。

## 为什么有效

门禁如果只有「Agent 被要求检查」，就存在两类作弊：作者假装验证过、作者替自己盖章。CI 让出具方变成机器（不可伪造），本 Skill 把这条衔接编进流程——部署有明确清单，判门有明确结论来源，无 CI 时有明确降级，不靠临场发挥。
