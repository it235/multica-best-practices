# CI/CD 与测试流水线（方法论）

> 本文件描述 Squad 流水线里 **G2.5（CI/CD 验证）** 与 **Tester 三阶段（T1 / T2 / T3）** 的方法论框架。CI/CD 结果统一写入项目仓库，不依赖远程平台、地址或凭据。

## 一、阶段总览

```text
G2 实现验收 PASS
  │ 各端 merge 到 deploy branch 并 push
  ▼
G2.5 CI/CD 部署（@DevOps，multica-artifact-cicd-sync）
  │ 构建部署到测试环境，回传环境 URL
  ▼
G3 测试验收（@Tester T3，multica-test-automation + multica-artifact-test-sync）
  │ 在部署环境跑自动化，出测试报告
  ▼
人类验收（G4）
```

**关键衔接**：G2.5 是 G3 的前置硬门禁。没有部署环境 URL，T3 不得开始（不得用本地 mock 替代部署环境验证）。@DevOps 与 @Tester 解耦——部署只产生环境，执行测试只消费环境。

## 二、Tester 三阶段

| 阶段 | 触发时机 | 产出 | 门禁 |
| --- | --- | --- | --- |
| **T1** 功能用例 | 设计定稿后，与 API 契约并行 | 功能用例 + 设计研读（落到团队用例平台） | Leader 判门 |
| **并行** 接口用例 | API 契约就绪后，与前后端实现并行 | 接口测试用例（供 T3 使用） | Leader 判门 |
| **T2** 补充 + 覆盖率 | G2 PASS 后、T3 前 | 用例补充清单 + 覆盖率评估（非测试报告） | Leader 判门 |
| **T3** 自动化执行 | **G2.5 PASS 后** | 自动化执行日志 + 测试报告（G3 输入） | G3（Leader 复核） |

T1 / T2 只写用例与评估，**不执行**；T3 是唯一执行阶段，且绑定真实部署环境。

## 三、deploy branch 模型

- Squad 在 G0 声明一个 **deploy branch**（默认 `release/<ISSUE-KEY>-<slug>`），所有实现端 merge 到它再 push。
- @DevOps 的 CI/CD **只认 deploy branch**，不认 feature 分支。
- 分仓多服务时，各 service 共用同一条 deploy branch（不要为前后端各猜一条 feature 分支）。

## 四、角色分工

| 角色 | 在流水线中的职责 |
| --- | --- |
| @Leader | 声明 deploy branch；G2 后确认各端已 merge 并 push；判 G2.5 与 G3 |
| @DevOps | G2 PASS + push 后，用 `multica-artifact-cicd-sync` 触发构建部署，回传环境 URL（不写业务代码） |
| @Tester | T1/T2 写用例与评估；G2.5 后 T3 在部署环境跑自动化 |
| @FrontendDev / @BackendDev | 实现并 merge 到 deploy branch，提供变更文件列表供 T2 评估 |

## 五、无 @DevOps / 无 CI 系统的退化路径

- 没有可触发的 CI/CD 时，**跳过 G2.5**，T3 退化为：本地 / 手动验证 + 显式标注「未走 CI/CD 部署」。证据要求不变——仍需给出环境 / 执行方式与输出。
- 这与门禁体系不冲突：G2.5 是「有 CI 时的硬门禁」，不是必走步骤。见 `gates-and-evidence.md`。

## 六、为什么有效

1. **部署与测试解耦**：DevOps 只生产环境，Tester 只消费环境，避免「自测自部署自宣称成功」。
2. **T1/T2 左移**：用例在设计 / 代码阶段就准备，实现完成即可执行，不等代码写完才开始想怎么测。
3. **G2.5 硬性衔接 T3**：测试必须基于真实部署环境，避免「开发机测过就当验收」。
4. **本地可复现**：构建、测试、打包命令及结果必须在项目仓库中可复核。

## 七、与 skill 三层架构的关系

```text
角色提示词（内容层）──「用 multica-artifact-cicd-sync 触发 CI/CD」
        │
编排层 multica-artifact-cicd-sync ── 调用 ──┐
        │                                   │
项目仓库构建配置 ──────────────────────────┘
```

团队接入自己内网时，只填平台层壳子里的 `config.yaml` 与 `scripts/`，上层零改动。
