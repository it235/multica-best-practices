# 协作产物约定

> 目的：多 Agent 协作时，下游必须能**稳定地找到上游产物**。本文规定每类产物的「内容规范」与「对接 skill」——**产物落在哪个平台、怎么传 / 取，全部交给 skill，不写进角色提示词**。这样换公司（平台不同）只换 skill，不动任何 agent。

## 1. 核心原则：内容归角色，平台归 skill

- **角色提示词只描述"产出什么内容"**（如 PRD 含哪些段落、API 契约含哪些字段），**不出现任何具体平台名**（Figma / Confluence / Apifox / Jira 等）。
- **落盘 / 上传 / 取回由 `multica-artifact-*-sync` 系列 skill 负责**。每个角色在提示词里只写一句"用 `multica-artifact-xxx-sync` skill 落地"，具体平台在该 skill 内实现，可替换。
- **稳定引用 = 链接或路径**：下游通过 skill 回传的链接 / 路径定位上游产物，而不是靠"你应该知道上游产了啥"。

## 1.1 三层架构：内容 / 编排 / 平台

为了让「换公司只换 skill」真正成立，产物落地拆为三层，越往下越内网化、越上层越可复制：

| 层 | 是谁 | 写什么 | 是否含内网细节 |
| --- | --- | --- | --- |
| **内容层** | 角色提示词（agents/*.md） | 产出什么内容（段落、字段、编号） | 否——永远不含平台名 |
| **编排层** | `multica-artifact-*-sync` skill | 把内容落地到某类产物（PRD / 设计 / API / 用例），并回传稳定引用 | 否——只声明"调哪个平台 skill"，不写地址 |
| **平台层** | `multica-platform-*` skill | 真正连系统：Wiki / Issue / CI / 测试工具 的读写 | **是——地址、空间、Job 名、凭据都在这里** |

**关键约束**：

1. 内容层（角色）绝不出现平台名；它只说"用 `multica-artifact-xxx-sync` skill 落地"。
2. 编排层（`multica-artifact-*-sync`）只调用平台层 skill，不写死任何 URL / pageId / Job 名。
3. 平台层（`multica-platform-*`）是**唯一允许**出现内网地址、空间 ID、凭据变量的地方；且凭据只走运行时 env，不写进任何提示词。

这样：公开仓库只放内容层 + 编排层 + 平台层**占位壳**；团队接入自己内网时，只填平台层壳子里的 `config.yaml` 与 `scripts/`，上层零改动。

### 标准用法（PM / Architect 双 skill 句式）

- **@ProductManager**：先用 `multica-requirement-analysis` 把 Issue 结构化为带编号的 PRD 内容，再用 `multica-artifact-req-sync` 编排落地（内部调用平台层）。
- **@Architect**：先用 `multica-technical-design` 写本地设计文档，再用 `multica-artifact-design-sync` 发布（内部调用平台层）。
- **@Tester**：先用 `multica-test-t1-design` 产出用例内容，再用 `multica-test-orchestration` 落地；T3 自动化用 `multica-test-t3-ui-automation`。

「分析 / 设计」类 skill 负责**内容**，「artifact-sync」类 skill 负责**落地与回传引用**——两者分离，内容可复用、平台可替换。

## 2. 产物 → 内容规范 → 对接 skill（一一对应）

| 产物 | 责任人 | 内容规范（角色侧） | 对接 skill（平台侧，可替换） |
| --- | --- | --- | --- |
| UI 设计 | @Designer | 页面结构、状态、交互、标注（对齐 PRD 信息架构） | `multica-artifact-ui-sync`（默认 Figma） |
| 产品需求 PRD | @ProductManager | G-/FR-/BR-/AC-/KPI-/RISK-/OP- 编号化需求 | `multica-artifact-req-sync`（默认 Wiki 平台） |
| 开发设计文档 | @Architect | 当前架构、最小改动、受影响组件、实现步骤、风险 | `multica-artifact-design-sync`（默认 Git 仓库 / Wiki 平台） |
| API 接口文档 | @BackendDev | 端点、入参 / 出参、错误码、鉴权、BR- 对应 | `multica-artifact-api-sync`（默认 API 工具） |
| 测试用例 / 报告 | @Tester | 功能 / 接口用例、覆盖 AC-、测试报告 | `multica-test-orchestration`（默认 用例平台） |
| CI/CD 部署 | @DevOps | 构建 / 部署记录、环境 URL、日志摘要 | `multica-artifact-cicd-sync`（默认 CI 系统） |

> 实现类产物（代码）在真实代码仓库，其变更文件列表写进对应阶段产物文件，由下游与门禁核对。

## 3. 角色侧写法（统一模板）

每个角色的「我产出什么」段落只写：

```text
产出 <产物名>，用 `multica-artifact-<xxx>-sync` skill 落地到团队约定平台，并回传稳定链接给 Leader。
内容规范见本文第 2 表 / 对应角色指令。
```

不写平台名、不写本地路径、不写"上传到 XXX"。

## 4. 下游引用的硬规则

1. 上游完成后，由 skill 回传**稳定链接 / 路径**；Leader 派活时显式带上该引用（如"读 `<PRD 链接>` 后做 X"），不靠口头约定。
2. 门禁判词引用产物用「链接 + 编号」（如「`<API 契约链接>` 的 BR-3 缺错误码」），不写"前面那个文档"。
3. 同一类产物永远用同一个 skill 落地——下游靠 skill 名称 + issue 标识定位，不靠搜索。
4. 产物被修改后，引用不变、内容更新；下游门禁据此重新判门（见 gates 的「产物变更门禁失效」）。

## 5. 与编号规范的关系

- 产物**内容**用 `gates-and-evidence.md` 的「AI 可读纪律」（稳定标题、稳定表字段、G-/FR-/BR-/AC- 编号）。
- 产物**位置**由 skill 决定（链接或路径）；位置与内容同样要稳定，下游才能机器化定位。

## 6. 平台替换（不改角色提示词）

团队换平台时，只改对应的 `multica-artifact-*-sync` skill 的「默认平台」段，把 Figma / Confluence / Apifox / Jira 换成你们的工具（蓝湖 / 语雀 / Swagger / TestRail 等），保持「上传 + 回传稳定引用」接口不变。全部角色提示词与 squad 指令**无需改动**。

## 7. 常见错误

Bad: "@Designer 把设计传到 Figma，链接发我。"（平台名固化进提示词，换公司就失效）

Better: "@Designer 产出 UI 设计，用 `multica-artifact-ui-sync` skill 落地并回传链接。"（平台在 skill 内，提示词可复制）
