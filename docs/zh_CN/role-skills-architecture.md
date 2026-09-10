# Skill 分层架构

> 回答一个问题：**一条能力该写成 Skill、写进 Agent Instructions，还是写进 Squad？**
> 以及：为什么平台 URL、凭据、REST 细节**永远不出现在角色提示词里**。

本文是 [artifact-conventions](./artifact-conventions.md) 中「三层架构」的完整论证，也是 `templates/zh_CN/skills/README.md` 索引的设计依据。

---

## 1. 为什么要分层

没有分层时，一个 Squad 会长成这样：

| 症状 | 后果 |
| --- | --- |
| JIRA / Confluence 的 REST 脚本在每个角色 skill 里各写一份 | 认证方式一变，全库改一遍 |
| 角色提示词里写着 Confluence 空间名、JIRA 项目 KEY | 换团队 / 换公司，整套模板失效 |
| 「产出什么」与「发到哪」写在同一份文档里 | 想换平台就得重读全部内容 |
| 评审标准和产出标准混在一起 | 完成者自审自放行，门禁形同虚设 |

分层只有一条原则：**变化频率不同的东西，不要写在一起。**

- 内容（怎么写一个好设计）几乎不变 → 内容层
- 平台（发到哪、怎么认证）每个团队都不一样 → 平台层
- 把两者接起来 → 编排层

---

## 2. 四层模型

```text
┌─ 内容层  content ──────────── 写什么、怎么算好 ────────────┐
│  multica-pm-requirement-spec / multica-technical-design   │
│  multica-backend-impl / multica-frontend-impl              │
│  multica-test-t1-design / -t2-coverage / -t3-*             │
└────────────────────────┬──────────────────────────────────┘
                         │ 按 skill 名调用
┌─ 编排层  orchestration ─┴── 产物落到团队平台并回传稳定链接 ─┐
│  multica-pm-artifact-publish / -design-sync / -api-sync      │
│  multica-design-ui-impl / -frontend / -cicd-sync         │
│  multica-test-orchestration（测试跨阶段路由）               │
└────────────────────────┬──────────────────────────────────┘
                         │ 按 skill 名调用
┌─ 平台层  platform ──────┴── 唯一连外部系统的一层 ──────────┐
│  multica-platform-confluence / -jira / -jenkins            │
│  multica-platform-apifox / -figma                          │
│  只在这里出现 URL、凭据、REST 细节                          │
└────────────────────────────────────────────────────────────┘

┌─ 评审层  review ───────── 由「非产出者」执行 ──────────────┐
│  multica-review-product / -architect / -designer           │
│  multica-review-frontend / -backend / -test                │
│  + multica-verification（Leader 判门，独立于评审）          │
└────────────────────────────────────────────────────────────┘
```

**判断该放哪层的方法**：问「这段内容会不会因为换个公司 / 换个平台而改写？」

- 会 → 平台层（或编排层的配置项）
- 不会 → 内容层
- 只是把两者连起来 → 编排层
- 是「别人来挑毛病」→ 评审层

---

## 3. Skill 清单（29 个）

### 内容层

| Skill | 挂载角色 | 职责 |
| --- | --- | --- |
| `multica-pm-requirement-spec` | ProductManager | 把需求结构化成编号 PRD |
| `multica-technical-design` | Architect | 技术设计草稿（含元数据与修订记录） |
| `multica-backend-impl` | BackendDev | 契约先行 + TDD 的后端实现 |
| `multica-frontend-impl` | FrontendDev | 体验与状态完整的前端实现 |
| `multica-test-t1-design` | Tester | T1 用例：追溯矩阵 + 覆盖维度 |
| `multica-test-t2-coverage` | Tester | T2 覆盖率评估（对照 T1 与实现 diff） |
| `multica-test-t3-ui-automation` | Tester | T3 UI 自动化（1 CASE = 1 test） |
| `multica-test-t3-api-automation` | Tester | T3 接口自动化跑批 |
| `multica-verification` | Leader | 门禁判定：证据齐不齐、AC 对不对 |


### 编排层

| Skill | 挂载角色 | 落地目标（可替换） |
| --- | --- | --- |
| `multica-pm-artifact-publish` | ProductManager | 需求平台（默认 Confluence + Issue） |
| `multica-artifact-architect` | Architect | 文档平台 / Git |
| `multica-artifact-backend` | BackendDev | API 平台（默认 Apifox） |
| `multica-design-ui-impl` | Designer | 设计平台（默认 Figma） |
| `multica-artifact-frontend` | FrontendDev | 文档平台 |
| `multica-artifact-cicd-sync` | DevOps | CI（默认 Jenkins）→ 回传部署 URL |
| `multica-test-orchestration` | Tester | 跨 T1/T2/T3 的路由与裁决 |

### 平台层

| Skill | 读 | 写 |
| --- | --- | --- |
| `multica-platform-jira` | issue、关联 issue、Confluence 链接 | 建 Story、流转、追加描述 / 链接 |
| `multica-platform-confluence` | 页面（URL / pageId → Markdown + 图片） | 创建 / 更新页面（Markdown / HTML） |
| `multica-platform-figma` | 文件元数据、设计摘要 | — |
| `multica-platform-apifox` | 场景 / 契约 | OpenAPI 同步、场景补充、跑批 |
| `multica-platform-jenkins` | 构建状态、日志 | 触发构建 / 发布 / 晋级 |
| `multica-platform-knowledge-base` | 知识库问答 | — |

> 平台层**只放占位外壳**：`config.yaml` 与 `.env.example` 里全是 `<JIRA_URL>`、`<JENKINS_URL>` 这类占位符，团队填自己的值即可。详见 [platform-collaboration](./platform-collaboration.md)。

### 评审层

| Skill | 评审者 | 评什么 |
| --- | --- | --- |
| `multica-review-product` | ProductReviewer | 价值 / 逻辑 / 清晰度 |
| `multica-review-architect` | ArchReviewer | 设计维度覆盖与阻断项 |
| `multica-review-designer` | DesignReviewer | UI 与需求对齐 |
| `multica-review-frontend` | FrontendReviewer | 边界态、影响面、8 个维度 |
| `multica-review-backend` | BackendReviewer | 契约、错误处理、兼容性 |
| `multica-review-test` | TestReviewer | 用例可执行性与覆盖真实性 |

### 工具

| Skill | 用途 |
| --- | --- |
| `multica-manage-skills` | 通过 Multica API 做运营统计 |

---

## 4. 角色 → Skill 挂载矩阵

| 角色 | 内容 | 编排 | 平台（仅编排层调用） |
| --- | --- | --- | --- |
| ProductManager | `multica-pm-requirement-spec` | `multica-pm-artifact-publish` | 经编排层 |
| Architect | `multica-technical-design` | `multica-artifact-architect` | 经编排层 |
| Designer | — | `multica-design-ui-impl` | 经编排层 |
| BackendDev | `multica-backend-impl` | `multica-artifact-backend` | 经编排层 |
| FrontendDev | `multica-frontend-impl` | `multica-artifact-frontend` | 经编排层 |
| Tester | `multica-test-orchestration` → T1/T2/T3 | 用例正文由 T1/T2 自发布 | 经编排层 |
| DevOps | — | `multica-artifact-cicd-sync` | `multica-platform-jenkins` |
| Leader | `multica-verification` | — | — |
| Reviewer | `multica-review-*` | — | — |

**注意最后两列**：只有 DevOps 直接挂平台 skill（因为它的工作就是操作 CI），其余角色一律**只挂内容 / 编排 skill**，平台由编排层按名调用。

---

## 5. 挂载约定

1. **按名挂载，不写路径**：Agent Instructions 里只写 `` `multica-xxx` ``，不写 `templates/...`。
2. **平台名不进角色提示词**：写「用 `multica-artifact-backend` 落地并回传稳定链接」，不写「发布到 Apifox」。
3. **凭据不进任何提示词**：一律走环境变量或平台 skill 的 `.env`，见 [SECURITY](../../SECURITY.md)。
4. **编排层不重复平台实现**：平台有的 REST 脚本，编排层只调不抄。

---

## 6. 常见错误

| Bad | Better |
| --- | --- |
| 在 Agent Instructions 里写「把设计文档发到 `<空间名>` 的 `<页面>` 下」 | 写「用 `multica-artifact-architect` 落地并回传链接」，父页配置留在平台 skill |
| 角色 skill 里自带一份 JIRA Basic 认证代码 | 删掉，改声明 `metadata.orchestrates: multica-platform-jira` |
| 让完成者自己评审自己的产物 | 评审由 `multica-review-*` + 非产出者执行，见 [gates-and-evidence](./gates-and-evidence.md) |
| 一个 skill 又写「用例该怎么写」又写「怎么连 JIRA 导入」 | 拆开：内容留 T1，连接留 platform；绑定具体测试工具的导入脚本留在团队自己的 T1 里 |

---

## 7. 延伸阅读

| 文档 | 内容 |
| --- | --- |
| [artifact-conventions](./artifact-conventions.md) | 产物内容规范 + 编排 skill 用法 |
| [platform-collaboration](./platform-collaboration.md) | 平台能力只写一份的具体约定 |
| [FLOW](./FLOW.md) | 交付物驱动的完整流程与门禁 |
| [where-to-put-things](./where-to-put-things.md) | 指令该放哪的速查表 |
