#!/bin/bash
# ============================================
# Confluence API 封装 (v2.2 - 配置驱动 + 老版本用户名密码认证)
# 从 .env 读凭据，从 config.yaml 读配置
# ============================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SKILL_DIR="$(dirname "$SCRIPT_DIR")"

# 加载 .env 并解析凭据（域账号优先）
# shellcheck disable=SC1091
source "$SCRIPT_DIR/credentials.sh"
load_skill_env "$SKILL_DIR"
resolve_credentials

# 加载 config.yaml（用 python 解析，因为 bash 处理 YAML 太痛苦）
parse_config() {
  local key="$1"
  python3 -c "
import yaml, sys
try:
    with open('$SKILL_DIR/config.yaml') as f:
        config = yaml.safe_load(f)
    keys = '$key'.split('.')
    val = config
    for k in keys:
        val = val[k]
    print(val)
except Exception as e:
    print(f'ERROR: {e}', file=sys.stderr)
    sys.exit(1)
" 2>/dev/null || echo ""
}

# 获取凭据
CONFLUENCE_URL="${CONFLUENCE_URL:-$(parse_config confluence.url 2>/dev/null || echo 'http://your-domain.atlassian.net/wiki:8090')}"
CONFLUENCE_TOKEN="${CONFLUENCE_TOKEN:-${CONFLUENCE_PAT:-}}"
CONFLUENCE_AUTH_MODE="${CONFLUENCE_AUTH_MODE:-basic}"  # basic | form | token
DEFAULT_SPACE="${DEFAULT_SPACE:-$(parse_config confluence.default_space 2>/dev/null || echo 'CRM')}"
DEFAULT_PARENT="${DEFAULT_PARENT:-$(parse_config confluence.default_parent_page_id 2>/dev/null || echo '125836668')}"

# 检查凭据
CURL_AUTH_ARGS=()
COOKIE_JAR=""

cleanup_auth() {
  if [ -n "$COOKIE_JAR" ] && [ -f "$COOKIE_JAR" ]; then
    rm -f "$COOKIE_JAR"
  fi
}
trap cleanup_auth EXIT

require_user_pass() {
  if [ -z "$CONFLUENCE_USER" ] || [ -z "$CONFLUENCE_PASS" ]; then
    echo "❌ 未配置凭据。请设置 JIRA_USERNAME / JIRA_PASSWORD，或在 .env 中设置 CONFLUENCE_USER 和 CONFLUENCE_PASS"
    exit 1
  fi
}

form_login() {
  require_user_pass
  COOKIE_JAR="$(mktemp "${TMPDIR:-/tmp}/confluence-cookie.XXXXXX")"

  local login_resp http_code
  login_resp=$(curl -s -w "\n%{http_code}" \
    -c "$COOKIE_JAR" \
    -X POST "$CONFLUENCE_URL/dologin.action" \
    --data-urlencode "os_username=$CONFLUENCE_USER" \
    --data-urlencode "os_password=$CONFLUENCE_PASS" \
    --data "os_cookie=true" \
    --data "os_destination=/rest/api/user/current" \
    --data "login=Log in")
  http_code=$(echo "$login_resp" | tail -1)

  if [ "$http_code" != "200" ] && [ "$http_code" != "302" ]; then
    echo "❌ Confluence 表单登录失败 (HTTP $http_code)"
    exit 1
  fi

  CURL_AUTH_ARGS=(-b "$COOKIE_JAR")
}

check_auth() {
  CURL_AUTH_ARGS=()

  case "$CONFLUENCE_AUTH_MODE" in
    basic)
      require_user_pass
      CURL_AUTH_ARGS=(--basic -u "$CONFLUENCE_USER:$CONFLUENCE_PASS")
      ;;
    form)
      form_login
      ;;
    token)
      if [ -z "$CONFLUENCE_TOKEN" ]; then
        echo "❌ CONFLUENCE_AUTH_MODE=token 但未配置 CONFLUENCE_TOKEN / CONFLUENCE_PAT"
        exit 1
      fi
      CURL_AUTH_ARGS=(-H "Authorization: Bearer $CONFLUENCE_TOKEN")
      ;;
    *)
      echo "❌ 未知 CONFLUENCE_AUTH_MODE: $CONFLUENCE_AUTH_MODE"
      echo "   可选值: basic, form, token"
      exit 1
      ;;
  esac
}

print_auth_hint() {
  local body="$1"
  if echo "$body" | grep -qiE 'AUTHENTICATION_DENIED|oauth|WWW-Authenticate'; then
    echo ""
    echo "认证提示：Confluence 拒绝了当前用户认证。"
    echo "本 skill 默认走老版本 Confluence 用户名密码 Basic Auth。"
    echo "如果浏览器能登录但 REST Basic 失败，可尝试 CONFLUENCE_AUTH_MODE=form，或确认 REST Basic 是否被服务端禁用。"
  fi
}

# ── 命令实现 ──────────────────────────────

create_page() {
  local title="${1:-}"
  local parent_id="${2:-$DEFAULT_PARENT}"
  local content="${3:-<p>空页面</p>}"
  local space="${4:-$DEFAULT_SPACE}"

  if [ -z "$title" ] || [ -z "$parent_id" ]; then
    echo "Usage: $0 create-page <title> [parent_id] [content] [space_key]"
    echo ""
    echo "当前默认值:"
    echo "  Space: $DEFAULT_SPACE"
    echo "  父页面ID: $DEFAULT_PARENT"
    exit 1
  fi

  check_auth

  local resp
  local payload
  payload=$(TITLE="$title" PARENT_ID="$parent_id" CONTENT="$content" SPACE="$space" python3 - <<'PY'
import json
import os

print(json.dumps({
    "type": "page",
    "title": os.environ["TITLE"],
    "ancestors": [{"id": os.environ["PARENT_ID"]}],
    "space": {"key": os.environ["SPACE"]},
    "body": {
        "storage": {
            "value": os.environ["CONTENT"],
            "representation": "storage",
        }
    },
}, ensure_ascii=False))
PY
)

  resp=$(curl -s -w "\n%{http_code}" "${CURL_AUTH_ARGS[@]}" \
    -X POST "$CONFLUENCE_URL/rest/api/content/" \
    -H "Content-Type: application/json" \
    -d "$payload")

  local http_code
  http_code=$(echo "$resp" | tail -1)
  local body
  body=$(echo "$resp" | sed '$d')

  if [ "$http_code" = "200" ] || [ "$http_code" = "201" ]; then
    local page_id title_out
    page_id=$(echo "$body" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])" 2>/dev/null || echo "unknown")
    title_out=$(echo "$body" | python3 -c "import sys,json; print(json.load(sys.stdin)['title'])" 2>/dev/null || echo "$title")
    echo "✅ Confluence 页面创建成功"
    echo "  标题: $title_out"
    echo "  ID: $page_id"
    echo "  链接: $CONFLUENCE_URL/pages/viewpage.action?pageId=$page_id"
  else
    echo "❌ 创建失败 (HTTP $http_code)"
    echo "$body"
    print_auth_hint "$body"
    exit 1
  fi
}

fetch_page() {
  local page_id="${1:-}"
  local output_dir="${2:-}"
  local jira_key="${3:-}"

  if [ -z "$page_id" ]; then
    echo "Usage: $0 fetch-page <page_id> [output_dir] [jira_key]"
    exit 1
  fi
  check_auth

  local args=(python3 "$SCRIPT_DIR/fetch_page.py" "$page_id")
  [ -n "$output_dir" ] && args+=(--output-dir "$output_dir")
  [ -n "$jira_key" ] && args+=(--jira-key "$jira_key")
  "${args[@]}"
}

get_page() {
  local page_id="${1:-}"

  if [ -z "$page_id" ]; then
    echo "Usage: $0 get-page <page_id>"
    exit 1
  fi
  check_auth

  curl -s "${CURL_AUTH_ARGS[@]}" \
    "$CONFLUENCE_URL/rest/api/content/$page_id?expand=body.storage" \
    | python3 -c "
import sys, json
d = json.load(sys.stdin)
print(f\"标题: {d.get('title', 'N/A')}\")
print(f\"ID: {d.get('id', 'N/A')}\")
print(f\"版本: {d.get('version', {}).get('number', 'N/A')}\")
print()
body = d.get('body', {}).get('storage', {}).get('value', '')
print(body)
"
}

list_pages() {
  local space="${1:-$DEFAULT_SPACE}"
  check_auth

  curl -s "${CURL_AUTH_ARGS[@]}" \
    "$CONFLUENCE_URL/rest/api/content?spaceKey=$space&type=page&limit=200" \
    | python3 -c "
import sys, json
data = json.load(sys.stdin)
for r in data.get('results', []):
    print(f\"{r['id']:>12}  {r['title']}\")
"
}

find_page() {
  local title="${1:-}"
  local space="${2:-$DEFAULT_SPACE}"

  if [ -z "$title" ]; then
    echo "Usage: $0 find-page <title> [space_key]"
    exit 1
  fi
  check_auth

  curl -s "${CURL_AUTH_ARGS[@]}" \
    "$CONFLUENCE_URL/rest/api/content?spaceKey=$space&type=page&limit=200" \
    | KEYWORD="$title" python3 -c "
import os
import sys, json
data = json.load(sys.stdin)
keyword = os.environ['KEYWORD'].lower()
for r in data.get('results', []):
    if keyword in r.get('title', '').lower():
        print(f\"{r['id']:>12}  {r['title']}\")
"
}

update_page() {
  local page_id="${1:-}"
  local content="${2:-}"

  if [ -z "$page_id" ] || [ -z "$content" ]; then
    echo "Usage: $0 update-page <page_id> <content>"
    exit 1
  fi
  check_auth

  # 先获取当前版本号
  local page_json current_version current_title
  page_json=$(curl -s "${CURL_AUTH_ARGS[@]}" \
    "$CONFLUENCE_URL/rest/api/content/$page_id")
  current_version=$(echo "$page_json" | python3 -c "import sys,json; print(json.load(sys.stdin)['version']['number'])")
  current_title=$(echo "$page_json" | python3 -c "import sys,json; print(json.load(sys.stdin)['title'])")

  local new_version=$((current_version + 1))
  local payload
  payload=$(PAGE_ID="$page_id" TITLE="$current_title" VERSION="$new_version" CONTENT="$content" python3 - <<'PY'
import json
import os

print(json.dumps({
    "id": os.environ["PAGE_ID"],
    "type": "page",
    "title": os.environ["TITLE"],
    "version": {"number": int(os.environ["VERSION"])},
    "body": {
        "storage": {
            "value": os.environ["CONTENT"],
            "representation": "storage",
        }
    },
}, ensure_ascii=False))
PY
)

  curl -s "${CURL_AUTH_ARGS[@]}" \
    -X PUT "$CONFLUENCE_URL/rest/api/content/$page_id" \
    -H "Content-Type: application/json" \
    -d "$payload" | python3 -c "import sys,json; d=json.load(sys.stdin); print(f\"✅ 页面已更新到版本 {d['version']['number']}\")"
}

list_spaces() {
  check_auth
  curl -s "${CURL_AUTH_ARGS[@]}" \
    "$CONFLUENCE_URL/rest/api/space" \
    | python3 -c "
import sys, json
data = json.load(sys.stdin)
for r in data.get('results', []):
    print(f\"{r['key']:>20}  {r['name']}\")
"
}

# ── 帮助 ──────────────────────────────────

show_help() {
  cat << 'HELP'
Confluence API Wrapper v2.2

用法: confluence.sh <命令> [参数]

命令:
  create-page <标题> [父页面ID] [内容] [Space]    创建新页面
  fetch-page <页面ID> [输出目录] [JIRA_KEY]       拉取页面为 Markdown
  get-page <页面ID>                                获取页面内容
  update-page <页面ID> <内容>                      更新页面
  list-pages [Space]                                列出空间内所有页面
  find-page <标题> [Space]                         按标题搜索页面
  list-spaces                                       列出所有空间
  help                                              显示此帮助

示例:
  confluence.sh create-page "产品需求-XXX" 125836668 "<h1>需求</h1>" CRM
  confluence.sh get-page 131429035
  confluence.sh find-page "概览看板"
  confluence.sh list-pages CRM

配置:
  凭据通过 .env 或环境变量设置（域账号优先）:
    JIRA_USERNAME, JIRA_PASSWORD
    CONFLUENCE_URL, CONFLUENCE_USER, CONFLUENCE_PASS
    CONFLUENCE_AUTH_MODE=basic   默认，老版本 Confluence 用户名密码 Basic Auth
    CONFLUENCE_AUTH_MODE=form    老版本表单登录 cookie 模式
    CONFLUENCE_AUTH_MODE=token   可选 Bearer Token 模式
  项目配置在 config.yaml 中:
    confluence.default_space, confluence.default_parent_page_id
HELP
}

# ── 主入口 ────────────────────────────────

case "${1:-help}" in
  create-page)    create_page "${2:-}" "${3:-}" "${4:-}" "${5:-}" ;;
  fetch-page)     fetch_page "${2:-}" "${3:-}" "${4:-}" ;;
  get-page)       get_page "${2:-}" ;;
  update-page)    update_page "${2:-}" "${3:-}" ;;
  list-pages)     list_pages "${2:-$DEFAULT_SPACE}" ;;
  find-page)      find_page "${2:-}" "${3:-}" ;;
  list-spaces)    list_spaces ;;
  help|--help|-h) show_help ;;
  *)
    echo "未知命令: ${1:-}"
    echo "运行 '$0 help' 查看帮助"
    exit 1
    ;;
esac
