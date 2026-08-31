# 产物约定：local-first 固定路径

多 Agent 协作中的全部阶段产物都写入项目仓库，版本化评审，并通过仓库相对路径交接。任何 artifact sync skill 都不得访问外部平台、读取凭据、发网络请求或回传 URL。

## 固定映射

| 产物 | Owner | Skill | 仓库相对路径 |
| --- | --- | --- | --- |
| PRD | @ProductManager | `multica-artifact-req-sync` | `artifacts/<issue-id>/prd.md` |
| 技术设计 | @Architect | `multica-artifact-design-sync` | `artifacts/<issue-id>/technical-design.md` |
| API 契约 | @BackendDev | `multica-artifact-api-sync` | `artifacts/<issue-id>/api-contract.md` |
| UI / 交互设计 | @Designer | `multica-artifact-ui-sync` | `artifacts/<issue-id>/ui-design.md` |
| 测试用例 / 报告 | @Tester | `multica-artifact-test-sync` | `artifacts/<issue-id>/test-cases.md` |
| CI/CD 结果 | @DevOps | `multica-artifact-cicd-sync` | `artifacts/<issue-id>/cicd-result.md` |

## 硬规则

1. 角色负责内容，artifact sync skill 负责写入固定路径。
2. Leader 派活时显式传入上游仓库相对路径；下游按路径读取，不靠搜索。
3. 禁止绝对路径、`..`、外部 URL 和“已上传”但无本地文件的回执。
4. 同一 Issue 更新时覆盖同一路径；内容变化后，相关下游门禁立即失效并重跑。
5. CI/CD skill 只记录仓库内可验证结果，不负责调用远程流水线。

## 为什么有效

固定路径让产物可发现、可 diff、可追溯，也使 starter 在没有账号、凭据和网络的环境中直接运行。

## 常见失败

- 只在评论中贴内容：必须写入固定文件。
- 回传本机绝对路径：必须转换为仓库相对路径。
- 使用外部链接替代正文：把必要内容写入项目仓库后再交接。
