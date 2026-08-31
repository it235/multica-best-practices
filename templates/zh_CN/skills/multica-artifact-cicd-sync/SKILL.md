---
name: multica-artifact-cicd-sync
description: Local-first：把CI/CD 结果保存为项目仓库内文件并只回传相对路径；无外部平台、凭据或网络依赖。
metadata:
  mode: local-only
  output: artifacts/<issue-id>/cicd-result.md
---

# Artifact · CI/CD 结果 Sync

## Purpose

把CI/CD 结果落地为项目仓库中的稳定、可评审产物。本 skill **只支持本地路径**：不访问外部平台，不读取凭据，不发网络请求，也不返回 URL。

## 固定契约

- 输入：已完成的 Markdown 产物。
- 输出：`artifacts/<issue-id>/cicd-result.md`。
- 回传：仅回传上述仓库相对路径；禁止绝对路径、`..` 和外部链接。
- 更新：同一 Issue 覆盖同一路径；内容变化后，下游门禁失效并重跑。

## Workflow

1. 生成 Markdown，至少包含：提交/分支、命令、检查、产物位置、环境与失败诊断。
2. 在仓库根目录创建 `artifacts/<issue-id>/`，写入 `cicd-result.md`。
3. 确认文件完整且已纳入版本控制。
4. 向 Leader 回传 `artifacts/<issue-id>/cicd-result.md`；下游按路径读取，不靠搜索。

## 常见失败

- 返回本机绝对路径：转换为仓库相对路径。
- 只在聊天中粘贴：写入固定文件形成版本化产物。
- 返回外部 URL：改为固定本地路径。

## 为什么有效

固定路径提供可发现性、版本审查和可复现性；移除平台适配器后，starter 无凭据、无网络即可 Copy · Paste · Run。
