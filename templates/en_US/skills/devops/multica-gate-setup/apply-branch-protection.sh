#!/usr/bin/env bash
# 应用分支保护规则：要求 delivery-gate CI 通过 + 独立审批后才能合入 main。
# 用法：修改下方占位符后运行 `bash apply-branch-protection.sh`
set -euo pipefail

OWNER="YOUR_OWNER"          # 改成你的 GitHub 组织/用户名
REPO="YOUR_REPO"            # 改成你的仓库名
BRANCH="main"               # 受保护分支

RULE=$(cat "$(dirname "$0")/branch-protection.json")

echo "🔒 Applying branch protection to $OWNER/$REPO@$BRANCH ..."
gh api -X PUT "repos/$OWNER/$REPO/branches/$BRANCH/protection" \
  --header "Accept: application/vnd.github+json" \
  --input - <<< "$RULE"

echo "✅ Done. 此后 PR 必须 CI 绿 + 独立审批才能合入。"
