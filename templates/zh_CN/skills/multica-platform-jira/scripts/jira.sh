#!/bin/bash
# ============================================
# JIRA API 封装 (v2.0 - 配置驱动)
# 从 .env 读凭据，从 config.yaml 读项目配置
# ============================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SKILL_DIR="$(dirname "$SCRIPT_DIR")"
CONFIG_FILE="$SKILL_DIR/config.yaml"

# ── 配置加载 ──────────────────────────────

# 加载 .env 并解析凭据（域账号优先）
# shellcheck disable=SC1091
source "$SCRIPT_DIR/credentials.sh"
load_skill_env "$SKILL_DIR"
resolve_credentials

# 用 Python 解析 YAML 配置
yaml_get() {
  python3 -c "
import yaml, sys
try:
    with open('$CONFIG_FILE') as f:
        config = yaml.safe_load(f)
    keys = '$1'.split('.')
    val = config
    for k in keys:
        if isinstance(val, dict):
            val = val[k]
        elif isinstance(val, list):
            val = val[int(k)]
        else:
            print(f'ERROR: cannot index into {type(val)}', file=sys.stderr)
            sys.exit(1)
    if isinstance(val, (dict, list)):
        print(yaml.dump(val, default_flow_style=False))
    else:
        print(val)
except Exception as e:
    print(f'CONFIG_ERROR: {e}', file=sys.stderr)
    sys.exit(1)
" 2>/dev/null
}

yaml_get_optional() {
  yaml_get "$1" 2>/dev/null | tr -d '\n' || true
}

JIRA_URL="${JIRA_URL:-$(yaml_get_optional jira.url)}"
JIRA_URL="${JIRA_URL:-http://your-domain.atlassian.net:8080}"
CONFLUENCE_URL="${CONFLUENCE_URL:-$(yaml_get_optional confluence.url)}"
CONFLUENCE_URL="${CONFLUENCE_URL:-http://your-domain.atlassian.net/wiki:8090}"

# 从 config.yaml 获取项目字段映射
get_project_field() {
  local project="$1"
  local field="$2"
  yaml_get "projects.$project.fields.$field.customId" | tr -d '\n'
}

field_key() {
  local project="$1"
  local field="$2"
  local custom_id
  custom_id=$(get_project_field "$project" "$field")
  printf 'customfield_%s' "$custom_id"
}

field_key_or_default() {
  local project="$1"
  local field="$2"
  local fallback="$3"
  local custom_id
  custom_id=$(yaml_get_optional "projects.$project.fields.$field.customId")
  if [ -n "$custom_id" ]; then
    printf 'customfield_%s' "$custom_id"
  else
    printf '%s' "$fallback"
  fi
}

workflow_field_key() {
  local project="$1"
  local field="$2"
  local fallback="$3"
  local custom_id
  custom_id=$(yaml_get_optional "projects.$project.workflow_fields.$field.customId")
  if [ -z "$custom_id" ]; then
    custom_id=$(yaml_get_optional "workflow_fields.$field.customId")
  fi
  custom_id="${custom_id:-$fallback}"
  printf 'customfield_%s' "$custom_id"
}

get_issue_project() {
  local issue_key="$1"
  printf '%s' "${issue_key%%-*}"
}

get_jira_issue_type_id() {
  local issue_type_id
  issue_type_id=$(yaml_get_optional jira.issue_type_id)
  printf '%s' "${issue_type_id:-10001}"
}

get_project_id() {
  local project="$1"
  yaml_get "projects.$project.id" | tr -d '\n'
}

get_project_default_epic() {
  local project="$1"
  yaml_get "projects.$project.default_epic" | tr -d '\n'
}

get_default() {
  yaml_get "defaults.$1" | tr -d '\n'
}

# 获取字段选项 ID
get_field_option_id() {
  local project="$1"
  local field="$2"
  local label="$3"
  python3 -c "
import yaml
with open('$CONFIG_FILE') as f:
    config = yaml.safe_load(f)
options = config['projects']['$project']['field_options']['$field']
for o in options:
    if o['label'] == '$label':
        print(o['id'])
        break
" 2>/dev/null
}

# ── 凭据检查 ──────────────────────────────

check_auth() {
  if [ -z "$JIRA_USER" ] || [ -z "$JIRA_PASS" ]; then
    echo "❌ 未配置凭据。请设置 JIRA_USERNAME / JIRA_PASSWORD，或在 .env 中设置 JIRA_USER 和 JIRA_PASS"
    exit 1
  fi
}

# ── 周报记录（OBSIDIAN 集成）──────────────

OBSIDIAN_ROOT="${OBSIDIAN_ROOT:-}"
JIRA_NOTIFY_RECORD_DIR="${JIRA_NOTIFY_RECORD_DIR:-${OBSIDIAN_ROOT:+$OBSIDIAN_ROOT/06-收件箱/jira-notify-records}}"
BASE_SERVICE_WEEKLY_DIR="${BASE_SERVICE_WEEKLY_DIR:-${OBSIDIAN_ROOT:+$OBSIDIAN_ROOT/06-收件箱/base-service-weekly-materials}}"
ROLLUP_CONFIG_PATH="${ROLLUP_CONFIG_PATH:-${OBSIDIAN_ROOT:+$OBSIDIAN_ROOT/tools/dingtalk_progress_bot/config.local.json}}"
ROLLUP_MAIN_PY="${ROLLUP_MAIN_PY:-${OBSIDIAN_ROOT:+$OBSIDIAN_ROOT/tools/dingtalk_progress_bot/main.py}}"

ensure_dirs() {
  if [ -z "$JIRA_NOTIFY_RECORD_DIR" ] || [ -z "$BASE_SERVICE_WEEKLY_DIR" ]; then
    return 1
  fi
  mkdir -p "$JIRA_NOTIFY_RECORD_DIR" "$BASE_SERVICE_WEEKLY_DIR"
}

sanitize_filename() {
  echo "$1" | tr '[:space:]' '-' | tr -cd '[:alnum:]-_' | cut -c1-40
}

record_notify_for_weekly() {
  local title="$1"
  local content="$2"
  local webhook_token="$3"
  local project_type="$4"
  local send_result="$5"

  if ! ensure_dirs; then
    return 0
  fi

  local now_date now_time unix_ts rand suffix msg_id short_title short_text
  now_date="$(date +%Y%m%d)"
  now_time="$(date '+%Y-%m-%d %H:%M:%S')"
  unix_ts="$(date +%s)"
  rand="$RANDOM"
  short_title="$(sanitize_filename "$title")"
  short_text="$(echo "$content" | tr '\n' ' ' | sed 's/[[:space:]]\+/ /g' | cut -c1-200)"
  suffix="${now_date}-${short_title}-${unix_ts}-${rand}"
  msg_id="jira-notify-${unix_ts}-${rand}"

  local record_json="$JIRA_NOTIFY_RECORD_DIR/${suffix}.notify.json"
  local record_md="$JIRA_NOTIFY_RECORD_DIR/${suffix}.notify.md"
  local weekly_json="$BASE_SERVICE_WEEKLY_DIR/${now_date}-${short_title}-${msg_id}.weekly.json"
  local weekly_md="$BASE_SERVICE_WEEKLY_DIR/${now_date}-${short_title}-${msg_id}.weekly.md"

  cat > "$record_json" << EOF
{
  "msg_id": "$msg_id",
  "received_at": "$now_time",
  "sender": "jira.sh",
  "sender_staff_id": "$JIRA_USER",
  "conversation_id": "dingtalk-webhook:$project_type",
  "conversation_title": "JIRA自动通知-$project_type",
  "conversation_type": "webhook",
  "receive_mode": "脚本直发",
  "message_type": "markdown",
  "text": "$short_text",
  "title": "$title",
  "project_type": "$project_type",
  "webhook_token_masked": "${webhook_token:0:6}***${webhook_token: -6}",
  "reason": "jira.sh notify-dingtalk 自动记录",
  "send_result": $send_result
}
EOF

  cat > "$record_md" << EOF
# JIRA 通知发送记录

- 时间：$now_time
- 来源：jira.sh / notify-dingtalk
- 项目类型：$project_type
- 标题：$title
- 内容摘要：$short_text

## 发送结果

\`\`\`json
$send_result
\`\`\`
EOF

  cat > "$weekly_json" << EOF
{
  "msg_id": "$msg_id",
  "received_at": "$now_time",
  "sender": "jira.sh",
  "conversation_title": "JIRA自动通知-$project_type",
  "receive_mode": "脚本直发",
  "text": "[$title] $short_text",
  "reason": "jira.sh notify-dingtalk 自动记录",
  "weekly_sync_reason": "jira.sh 发钉钉通知成功后自动入周报素材"
}
EOF

  cat > "$weekly_md" << EOF
# 个人助手基础服务组周报素材记录

- 接收时间：$now_time
- 渠道：JIRA自动通知
- 会话标题：JIRA自动通知-$project_type
- 会话类型：webhook
- 接收方式：脚本直发
- 发送人：jira.sh
- 消息类型：markdown
- 记录轨道：base-service-weekly-materials
- 分类结果：工作事项
- 记录栏目：工作事项
- 识别依据：jira.sh 发钉钉通知成功后自动入周报素材
- 是否同步基础服务组周报素材：是
- 基础服务组周报同步依据：jira.sh 发钉钉通知成功后自动入周报素材

## 周报素材文本

[$title] $short_text
EOF

  if [ -n "$ROLLUP_MAIN_PY" ] && [ -n "$ROLLUP_CONFIG_PATH" ] && [ -f "$ROLLUP_MAIN_PY" ] && [ -f "$ROLLUP_CONFIG_PATH" ]; then
    python3 "$ROLLUP_MAIN_PY" --config "$ROLLUP_CONFIG_PATH" --rebuild-rollups >/dev/null 2>&1 || true
  fi
}

# ── 命令实现 ──────────────────────────────

# 创建 Story（通用版，--project 指定项目）
create_story() {
  local project="" summary="" description="" epic_link=""
  local need_user="" background=""
  local center_source="" region_source="" req_type="" compliance=""

  # 解析参数
  while [ $# -gt 0 ]; do
    case "$1" in
      --project)       project="$2"; shift 2 ;;
      --summary)       summary="$2"; shift 2 ;;
      --description)   description="$2"; shift 2 ;;
      --epic)          epic_link="$2"; shift 2 ;;
      --need-user)     need_user="$2"; shift 2 ;;
      --background)    background="$2"; shift 2 ;;
      --center-source) center_source="$2"; shift 2 ;;
      --region-source) region_source="$2"; shift 2 ;;
      --req-type)      req_type="$2"; shift 2 ;;
      --compliance)    compliance="$2"; shift 2 ;;
      *) shift ;;
    esac
  done

  if [ -z "$project" ] || [ -z "$summary" ]; then
    echo "Usage: $0 create-story --project <PROJ|MDP> --summary \"标题\" [其他选项]"
    echo ""
    echo "必填:"
    echo "  --project       项目代码 (PROJ 或 MDP)"
    echo "  --summary       Story 标题"
    echo ""
    echo "可选（未指定时使用 config.yaml 默认值）:"
    echo "  --description   描述内容"
    echo "  --epic          Epic Link Key"
    echo "  --need-user     需求人用户名"
    echo "  --background    需求背景"
    echo "  --center-source 需求来源（中心级）"
    echo "  --region-source 需求来源（区域）"
    echo "  --req-type      需求类型"
    echo "  --compliance    是否涉及合规"
    exit 1
  fi

  check_auth

  # 应用默认值
  local project_id epic_key issue_type_id
  project_id=$(yaml_get_optional "projects.$project.id")
  issue_type_id=$(get_jira_issue_type_id)
  epic_key="${epic_link:-$(yaml_get_optional "projects.$project.default_epic")}"
  need_user="${need_user:-$(get_default need_user)}"
  background="${background:-$(get_default background)}"
  center_source="${center_source:-$(get_default center_source)}"
  region_source="${region_source:-$(get_default region_source)}"
  req_type="${req_type:-$(get_default req_type)}"
  compliance="${compliance:-$(get_default compliance)}"

  if [ -z "$project_id" ]; then
    echo "❌ 未知项目: $project"
    echo "   可用项目: $(yaml_get projects | grep -E '^  [A-Z]+:' | sed 's/:$//' | tr '\n' ' ')"
    exit 1
  fi

  # 查找选项 ID
  local center_id region_id type_id compliance_id
  center_id=$(get_field_option_id "$project" center_source "$center_source")
  region_id=$(get_field_option_id "$project" region_source "$region_source")
  type_id=$(get_field_option_id "$project" req_type "$req_type")
  compliance_id=$(get_field_option_id "$project" compliance "$compliance")

  if [ -z "$center_id" ] || [ -z "$region_id" ] || [ -z "$type_id" ] || [ -z "$compliance_id" ]; then
    echo "❌ 字段选项未匹配，请检查 config.yaml 中的 field_options"
    echo "  center_source=$center_source -> $center_id"
    echo "  region_source=$region_source -> $region_id"
    echo "  req_type=$req_type -> $type_id"
    echo "  compliance=$compliance -> $compliance_id"
    exit 1
  fi

  echo "📋 准备创建 JIRA Story:"
  echo "  项目: $project (ID: $project_id)"
  echo "  Issue Type: $issue_type_id"
  echo "  标题: $summary"
  echo "  Epic: $epic_key"
  echo "  需求人: $need_user"
  echo "  中心来源: $center_source (ID: $center_id)"
  echo "  区域来源: $region_source (ID: $region_id)"
  echo "  需求类型: $req_type (ID: $type_id)"
  echo "  合规: $compliance (ID: $compliance_id)"
  echo ""

  # 构建 payload
  local payload need_user_field background_field center_source_field region_source_field req_type_field compliance_field epic_field
  need_user_field=$(field_key "$project" need_user)
  background_field=$(field_key "$project" background)
  center_source_field=$(field_key "$project" center_source)
  region_source_field=$(field_key "$project" region_source)
  req_type_field=$(field_key "$project" req_type)
  compliance_field=$(field_key "$project" compliance)
  epic_field=$(field_key "$project" epic_link)

  payload=$(PROJECT_ID="$project_id" \
    ISSUE_TYPE_ID="$issue_type_id" \
    SUMMARY="$summary" \
    DESCRIPTION="${description:-}" \
    NEED_USER="$need_user" \
    BACKGROUND="$background" \
    CENTER_ID="$center_id" \
    REGION_ID="$region_id" \
    TYPE_ID="$type_id" \
    COMPLIANCE_ID="$compliance_id" \
    EPIC_KEY="$epic_key" \
    NEED_USER_FIELD="$need_user_field" \
    BACKGROUND_FIELD="$background_field" \
    CENTER_SOURCE_FIELD="$center_source_field" \
    REGION_SOURCE_FIELD="$region_source_field" \
    REQ_TYPE_FIELD="$req_type_field" \
    COMPLIANCE_FIELD="$compliance_field" \
    EPIC_FIELD="$epic_field" \
    python3 - <<'PY'
import json
import os

payload = {
    'fields': {
        'project': {'id': os.environ['PROJECT_ID']},
        'issuetype': {'id': os.environ['ISSUE_TYPE_ID']},
        'summary': os.environ['SUMMARY'],
        'description': os.environ.get('DESCRIPTION', ''),
        os.environ['NEED_USER_FIELD']: {'name': os.environ['NEED_USER']},
        os.environ['BACKGROUND_FIELD']: os.environ['BACKGROUND'],
        os.environ['CENTER_SOURCE_FIELD']: [{'id': os.environ['CENTER_ID']}],
        os.environ['REGION_SOURCE_FIELD']: {'id': os.environ['REGION_ID']},
        os.environ['REQ_TYPE_FIELD']: [{'id': os.environ['TYPE_ID']}],
        os.environ['COMPLIANCE_FIELD']: {'id': os.environ['COMPLIANCE_ID']},
        os.environ['EPIC_FIELD']: os.environ['EPIC_KEY'],
    }
}
print(json.dumps(payload, ensure_ascii=False))
PY
)

  # 发送请求
  local resp http_code
  resp=$(curl -s -w "\n%{http_code}" -u "$JIRA_USER:$JIRA_PASS" \
    -X POST "$JIRA_URL/rest/api/2/issue/" \
    -H "Content-Type: application/json" \
    -d "$payload")

  http_code=$(echo "$resp" | tail -1)
  local body
  body=$(echo "$resp" | sed '$d')

  if [ "$http_code" = "200" ] || [ "$http_code" = "201" ]; then
    local issue_key
    issue_key=$(echo "$body" | python3 -c "import sys,json; print(json.load(sys.stdin)['key'])" 2>/dev/null)
    echo "✅ JIRA Story 创建成功: $issue_key"
    echo "   链接: $JIRA_URL/browse/$issue_key"
    echo "$issue_key"  # 输出 key 供后续使用
  else
    echo "❌ 创建失败 (HTTP $http_code)"
    echo "$body" | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    if 'errors' in d:
        for k, v in d['errors'].items():
            print(f'  {k}: {v}')
except: print(sys.stdin.read())
" 2>/dev/null || echo "$body"
    exit 1
  fi
}

# 获取 Issue
get_issue() {
  local key="$1"
  if [ -z "$key" ]; then echo "Usage: $0 get-issue <ISSUE_KEY>"; exit 1; fi
  check_auth

  curl -s -u "$JIRA_USER:$JIRA_PASS" "$JIRA_URL/rest/api/2/issue/$key" \
    | python3 -c "
import sys, json
d = json.load(sys.stdin)
f = d.get('fields', {})
print(f\"Key:     {d['key']}\")
print(f\"标题:    {f.get('summary', 'N/A')}\")
print(f\"状态:    {f.get('status', {}).get('name', 'N/A')}\")
print(f\"类型:    {f.get('issuetype', {}).get('name', 'N/A')}\")
print(f\"项目:    {f.get('project', {}).get('name', 'N/A')}\")
assignee = f.get('assignee')
print(f\"经办人:  {assignee.get('displayName', '未分配') if assignee else '未分配'}\")
print()
print(f.get('description', '无描述'))
"
}

# 从 Issue 描述 / 远程链接解析 Confluence 页面 URL 或 pageId
get_confluence_url() {
  local key="$1"
  local format="${2:-text}"  # text | json
  if [ -z "$key" ]; then
    echo "Usage: $0 get-confluence-url <ISSUE_KEY> [text|json]"
    exit 1
  fi
  check_auth
  export JIRA_URL JIRA_USER JIRA_PASS

  ISSUE_KEY="$key" OUTPUT_FORMAT="$format" python3 <<'PY'
import json, os, re, sys, urllib.request, base64

key = os.environ["ISSUE_KEY"]
fmt = os.environ.get("OUTPUT_FORMAT", "text")
base = os.environ["JIRA_URL"].rstrip("/")
auth = base64.b64encode(f"{os.environ['JIRA_USER']}:{os.environ['JIRA_PASS']}".encode()).decode()
headers = {"Authorization": f"Basic {auth}", "Accept": "application/json"}

def fetch(path):
    req = urllib.request.Request(f"{base}{path}", headers=headers)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)

issue = fetch(f"/rest/api/2/issue/{key}?fields=description")
desc = (issue.get("fields") or {}).get("description") or ""

urls = re.findall(r"https?://[^\s\]|]+confluence[^\s\]|>]+", desc, re.I)
urls += re.findall(r"https?://[^\s\]|]+/pages/viewpage\.action\?pageId=\d+", desc, re.I)
page_ids = re.findall(r"pageId=(\d+)", desc, re.I)

try:
    links = fetch(f"/rest/api/2/issue/{key}/remotelink")
    for item in links:
        url = (item.get("object") or {}).get("url") or ""
        if "confluence" in url.lower() or "pageId=" in url:
            urls.append(url)
            m = re.search(r"pageId=(\d+)", url)
            if m:
                page_ids.append(m.group(1))
except Exception:
    pass

urls = list(dict.fromkeys(urls))
page_ids = list(dict.fromkeys(page_ids))
result = {"issue_key": key, "urls": urls, "page_ids": page_ids}

if fmt == "json":
    print(json.dumps(result, ensure_ascii=False, indent=2))
else:
    if not urls and not page_ids:
        print(f"No Confluence link found in {key}")
        sys.exit(1)
    for u in urls:
        print(u)
    for pid in page_ids:
        if not any(pid in u for u in urls):
            print(f"pageId={pid}")
PY
}

# 追加 Wiki 格式内容到 Issue 描述（用于回写设计文档链接等）
append_description() {
  local key="$1"
  local wiki_block="$2"
  if [ -z "$key" ] || [ -z "$wiki_block" ]; then
    echo "Usage: $0 append-description <ISSUE_KEY> '<wiki_block>'"
    echo "Example: $0 append-description PROJ-1813 \$'h3. 设计文档\\n* [设计|http://...]'"
    exit 1
  fi
  check_auth
  export JIRA_URL JIRA_USER JIRA_PASS

  ISSUE_KEY="$key" WIKI_BLOCK="$wiki_block" python3 <<'PY'
import json, os, sys, urllib.request, base64

key = os.environ["ISSUE_KEY"]
wiki = os.environ["WIKI_BLOCK"]
url_base = os.environ.get("JIRA_URL", "")
user = os.environ.get("JIRA_USER", "")
password = os.environ.get("JIRA_PASS", "")
if not url_base or not user or not password:
    print("ERROR: missing JIRA_URL / credentials", file=sys.stderr)
    sys.exit(2)

auth = base64.b64encode(f"{user}:{password}".encode()).decode()
headers = {"Authorization": f"Basic {auth}", "Accept": "application/json"}

req = urllib.request.Request(
    f"{url_base.rstrip('/')}/rest/api/2/issue/{key}?fields=description",
    headers=headers,
)
with urllib.request.urlopen(req, timeout=30) as resp:
    data = json.load(resp)
desc = data.get("fields", {}).get("description") or ""
new_desc = desc + wiki
payload = json.dumps({"fields": {"description": new_desc}}).encode()
put_req = urllib.request.Request(
    f"{url_base.rstrip('/')}/rest/api/2/issue/{key}",
    data=payload,
    headers={**headers, "Content-Type": "application/json"},
    method="PUT",
)
with urllib.request.urlopen(put_req, timeout=30) as resp:
    resp.read()
print(f"OK appended description to {key}")
PY
}

# JQL 搜索
search_issues() {
  local jql="$1"
  local max="${2:-20}"
  if [ -z "$jql" ]; then echo "Usage: $0 search <JQL> [max_results]"; exit 1; fi
  check_auth

  curl -s -u "$JIRA_USER:$JIRA_PASS" \
    "$JIRA_URL/rest/api/2/search?jql=$(echo "$jql" | python3 -c "import sys,urllib.parse; print(urllib.parse.quote(sys.stdin.read()))")&maxResults=$max" \
    | python3 -c "
import sys, json
d = json.load(sys.stdin)
for issue in d.get('issues', []):
    f = issue['fields']
    print(f\"{issue['key']:>12}  [{f.get('status',{}).get('name','?'):>6}]  {f.get('summary','')}\")
print(f\"\n共 {d.get('total', 0)} 条结果\")
"
}

# 查看可编辑字段
get_fields() {
  local key="$1"
  if [ -z "$key" ]; then echo "Usage: $0 get-fields <ISSUE_KEY>"; exit 1; fi
  check_auth

  curl -s -u "$JIRA_USER:$JIRA_PASS" "$JIRA_URL/rest/api/2/issue/$key/editmeta" \
    | python3 -c "
import sys, json
d = json.load(sys.stdin)
for name, field in d.get('fields', {}).items():
    required = '✅' if field.get('required') else '  '
    ftype = field.get('schema', {}).get('type', '?')
    print(f'{required} {name:>25}  ({ftype})')
"
}

# 获取 Epic 列表
get_epics() {
  local project_name="${1:-Angelalign Intellect}"
  check_auth

  curl -s -u "$JIRA_USER:$JIRA_PASS" \
    "$JIRA_URL/rest/api/2/search?jql=project=%22$(echo "$project_name" | python3 -c "import sys,urllib.parse; print(urllib.parse.quote(sys.stdin.read()))")%22%20AND%20issuetype=Epic&maxResults=50" \
    | python3 -c "
import sys, json
d = json.load(sys.stdin)
for issue in d.get('issues', []):
    print(f\"{issue['key']:>12}  {issue['fields'].get('summary', '')}\")
"
}

# 列出所有项目
list_projects() {
  check_auth
  curl -s -u "$JIRA_USER:$JIRA_PASS" "$JIRA_URL/rest/api/2/project" \
    | python3 -c "
import sys, json
for p in json.load(sys.stdin):
    print(f\"{p['key']:>10}  {p['name']}\")
"
}

# 获取可用状态转换
get_transitions() {
  local key="$1"
  if [ -z "$key" ]; then echo "Usage: $0 get-transitions <ISSUE_KEY>"; exit 1; fi
  check_auth

  curl -s -u "$JIRA_USER:$JIRA_PASS" "$JIRA_URL/rest/api/2/issue/$key/transitions" \
    | python3 -c "
import sys, json
d = json.load(sys.stdin)
for t in d.get('transitions', []):
    print(f\"  ID={t['id']:>4}  → {t['to']['name']}\")
"
}

# 状态流转
transition() {
  local key="$1"
  local target="$2"
  local sprint_id="${3:-}"
  local design_hours="${4:-}"

  if [ -z "$key" ] || [ -z "$target" ]; then
    echo "Usage: $0 transition <ISSUE_KEY> <目标状态> [sprint_id] [design_hours]"
    echo ""
    echo "目标状态示例: 已完成, 进行中, 已评审, 未开始, 取消, 需求已排期"
    exit 1
  fi
  check_auth

  # 获取可用转换
  local transitions
  transitions=$(curl -s -u "$JIRA_USER:$JIRA_PASS" "$JIRA_URL/rest/api/2/issue/$key/transitions")

  # 匹配目标状态
  local tid
  tid=$(echo "$transitions" | python3 -c "
import sys, json
target = '$target'.strip()
ts = json.load(sys.stdin).get('transitions', [])

# 优先级匹配: name 精确 → to.name 精确 → name 包含 → to.name 包含
for t in ts:
    if t.get('name', '') == target:
        print(t['id']); sys.exit(0)
for t in ts:
    if t.get('to', {}).get('name', '') == target:
        print(t['id']); sys.exit(0)
for t in ts:
    if target in t.get('name', ''):
        print(t['id']); sys.exit(0)
for t in ts:
    if target in t.get('to', {}).get('name', ''):
        print(t['id']); sys.exit(0)
print('', file=sys.stderr)
sys.exit(1)
" 2>/dev/null)

  if [ -z "$tid" ]; then
    echo "❌ 找不到到 '$target' 的状态转换"
    echo "可用转换:"
    echo "$transitions" | python3 -c "
import sys, json
for t in json.load(sys.stdin).get('transitions', []):
    print(f\"  ID={t['id']:>4}  → {t['to']['name']}\")
"
    exit 1
  fi

  # 可选：先更新 Sprint / 设计时间字段
  if [ -n "$sprint_id" ] || [ -n "$design_hours" ]; then
    local project sprint_field design_hours_field
    project=$(get_issue_project "$key")
    sprint_field=$(workflow_field_key "$project" sprint "10004")
    design_hours_field=$(workflow_field_key "$project" design_hours "15700")

    local field_updates="{"
    [ -n "$sprint_id" ] && field_updates="$field_updates \"$sprint_field\": $sprint_id,"
    [ -n "$design_hours" ] && field_updates="$field_updates \"$design_hours_field\": $design_hours,"
    field_updates="${field_updates%,} }"

    curl -s -u "$JIRA_USER:$JIRA_PASS" -X PUT "$JIRA_URL/rest/api/2/issue/$key" \
      -H "Content-Type: application/json" \
      -d "{\"fields\": $field_updates}" > /dev/null
    echo "  字段已更新: sprint=${sprint_id:-未设置}, 设计时间=${design_hours:-未设置}"
  fi

  # 执行转换
  local resp
  resp=$(curl -s -u "$JIRA_USER:$JIRA_PASS" -X POST "$JIRA_URL/rest/api/2/issue/$key/transitions" \
    -H "Content-Type: application/json" \
    -d "{\"transition\": {\"id\": \"$tid\"}}")

  if [ -z "$resp" ]; then
    echo "✅ 状态已变更为: $target"
  elif echo "$resp" | python3 -c "import sys,json; d=json.load(sys.stdin); sys.exit(0 if not d.get('errors') and not d.get('errorMessages') else 1)" 2>/dev/null; then
    echo "✅ 状态已变更为: $target"
  else
    echo "❌ 状态变更失败"
    echo "$resp" | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    for k, v in d.get('errors', {}).items():
        print(f'  {k}: {v}')
    for m in d.get('errorMessages', []):
        print(f'  {m}')
except:
    print(sys.stdin.read())
" 2>/dev/null || echo "$resp"
    exit 1
  fi
}

# 需求排期
schedule() {
  local key="$1"
  local test_owner="$2"
  local est_test="$3"
  local est_release="$4"

  if [ -z "$key" ] || [ -z "$test_owner" ] || [ -z "$est_test" ] || [ -z "$est_release" ]; then
    echo "Usage: $0 schedule <ISSUE_KEY> <测试Owner> <预计提测日期> <预计发布日期>"
    echo ""
    echo "示例: $0 schedule PROJ-123 wangkang 2026-05-08 2026-05-14"
    exit 1
  fi
  check_auth

  # 更新排期字段
  echo "📅 更新排期字段..."
  local project test_owner_field est_release_field est_test_field payload
  project=$(get_issue_project "$key")
  test_owner_field=$(workflow_field_key "$project" test_owner "14301")
  est_release_field=$(workflow_field_key "$project" estimated_release_date "12500")
  est_test_field=$(workflow_field_key "$project" estimated_test_date "14303")

  payload=$(TEST_OWNER_FIELD="$test_owner_field" \
    EST_RELEASE_FIELD="$est_release_field" \
    EST_TEST_FIELD="$est_test_field" \
    TEST_OWNER="$test_owner" \
    EST_RELEASE="$est_release" \
    EST_TEST="$est_test" \
    python3 - <<'PY'
import json
import os

print(json.dumps({
    "fields": {
        os.environ["TEST_OWNER_FIELD"]: {"name": os.environ["TEST_OWNER"]},
        os.environ["EST_RELEASE_FIELD"]: os.environ["EST_RELEASE"],
        os.environ["EST_TEST_FIELD"]: os.environ["EST_TEST"],
    }
}, ensure_ascii=False))
PY
)

  curl -s -u "$JIRA_USER:$JIRA_PASS" -X PUT "$JIRA_URL/rest/api/2/issue/$key" \
    -H "Content-Type: application/json" \
    -d "$payload" > /dev/null
  echo "  ✅ 测试Owner: $test_owner"
  echo "  ✅ 预计提测: $est_test"
  echo "  ✅ 预计发布: $est_release"

  # 执行"需求已排期"转换
  echo ""
  transition "$key" "需求已排期"
}

# 钉钉通知
notify_dingtalk() {
  local title="$1"
  local content="$2"
  local webhook_token="${3:-}"
  local project_type="${4:-unknown}"

  if [ -z "$title" ] || [ -z "$content" ]; then
    echo "Usage: $0 notify-dingtalk <标题> <内容> [webhook_token] [project_type]"
    exit 1
  fi

  # 如果没传 webhook token，从 .env 中查找
  if [ -z "$webhook_token" ]; then
    webhook_token="${DINGTALK_PROJ_WEBHOOK:-${DINGTALK_MDP_WEBHOOK:-}}"
  fi

  if [ -z "$webhook_token" ]; then
    echo "❌ 未配置钉钉 Webhook Token"
    echo "   请在 .env 中设置 DINGTALK_PROJ_WEBHOOK 或 DINGTALK_MDP_WEBHOOK"
    exit 1
  fi

  local webhook="https://oapi.dingtalk.com/robot/send?access_token=$webhook_token"

  local payload
  payload=$(TITLE="$title" CONTENT="$content" python3 - <<'PY'
import json
import os

title = os.environ["TITLE"]
content = os.environ["CONTENT"]
print(json.dumps({
    'msgtype': 'markdown',
    'markdown': {
        'title': title,
        'text': f'### {title}\n\n{content}'
    }
}, ensure_ascii=False))
PY
)

  local result errcode
  result=$(curl -s -X POST "$webhook" -H "Content-Type: application/json" -d "$payload")
  errcode=$(echo "$result" | python3 -c "import sys,json; print(json.load(sys.stdin).get('errcode', -1))" 2>/dev/null)

  if [ "$errcode" = "0" ]; then
    echo "✅ 钉钉通知发送成功"
    record_notify_for_weekly "$title" "$content" "$webhook_token" "$project_type" "$result"
  else
    echo "❌ 钉钉通知发送失败: $result"
  fi
}

jira_json_field() {
  local field="$1"
  local mode="${2:-string}"
  FIELD="$field" MODE="$mode" python3 -c '
import json
import os
import sys

data = json.load(sys.stdin)
fields = data.get("fields", {})
value = fields.get(os.environ["FIELD"])
mode = os.environ.get("MODE", "string")

def text(v):
    if v is None:
        return ""
    return str(v)

if mode == "user":
    if isinstance(value, dict):
        print(value.get("name") or value.get("displayName") or "")
    else:
        print("")
elif mode == "array_value":
    first = value[0] if isinstance(value, list) and value else None
    if isinstance(first, dict):
        print(first.get("value") or first.get("name") or first.get("id") or "")
    else:
        print(text(first))
elif mode == "object_value":
    if isinstance(value, dict):
        print(value.get("value") or value.get("name") or value.get("id") or "")
    else:
        print(text(value))
else:
    print(text(value))
'
}

# 从 JIRA 和 Confluence 读取信息并发送通知
notify_story() {
  local jira_key="$1"
  local confluence_id="${2:-}"
  local project_type="${3:-aai}"
  local project_type_upper
  project_type_upper=$(echo "$project_type" | tr '[:lower:]' '[:upper:]')

  if [ -z "$jira_key" ]; then
    echo "Usage: $0 notify-story <JIRA_KEY> [confluence_page_id] [aai|mdp]"
    exit 1
  fi
  check_auth

  # 获取 webhook token
  local webhook_env_var="DINGTALK_${project_type_upper}_WEBHOOK"
  local webhook_token="${!webhook_env_var:-}"

  if [ -z "$webhook_token" ]; then
    echo "❌ 未配置钉钉 Webhook Token: $webhook_env_var"
    echo "   请在 .env 中配置，或通过环境变量传入"
    exit 1
  fi

  # 读取 JIRA 信息
  local jira_data project need_user_field center_source_field region_source_field req_type_field compliance_field epic_field
  project=$(get_issue_project "$jira_key")
  need_user_field=$(field_key_or_default "$project" need_user "customfield_11700")
  center_source_field=$(field_key_or_default "$project" center_source "customfield_14700")
  region_source_field=$(field_key_or_default "$project" region_source "customfield_16100")
  req_type_field=$(field_key_or_default "$project" req_type "customfield_14305")
  compliance_field=$(field_key_or_default "$project" compliance "customfield_14602")
  epic_field=$(field_key_or_default "$project" epic_link "customfield_10000")

  jira_data=$(curl -s -u "$JIRA_USER:$JIRA_PASS" \
    "$JIRA_URL/rest/api/2/issue/$jira_key?fields=summary,description,$need_user_field,$center_source_field,$region_source_field,$req_type_field,$compliance_field,$epic_field")

  local summary desc need_user center_source region_source req_type compliance epic
  summary=$(echo "$jira_data" | jira_json_field summary string 2>/dev/null)
  desc=$(echo "$jira_data" | jira_json_field description string 2>/dev/null | sed 's/<[^>]*>//g' | tr '\n' ' ' | cut -c1-200)
  need_user=$(echo "$jira_data" | jira_json_field "$need_user_field" user 2>/dev/null)
  center_source=$(echo "$jira_data" | jira_json_field "$center_source_field" array_value 2>/dev/null)
  region_source=$(echo "$jira_data" | jira_json_field "$region_source_field" object_value 2>/dev/null)
  req_type=$(echo "$jira_data" | jira_json_field "$req_type_field" array_value 2>/dev/null)
  compliance=$(echo "$jira_data" | jira_json_field "$compliance_field" object_value 2>/dev/null)
  epic=$(echo "$jira_data" | jira_json_field "$epic_field" string 2>/dev/null)

  # 读取 Confluence 背景
  local confluence_bg="无"
  if [ -z "$confluence_id" ]; then
    confluence_id=$(echo "$desc" | grep -o 'pageId=[0-9]*' | head -1 | cut -d= -f2)
  fi
  if [ -n "$confluence_id" ] && [ -n "${CONFLUENCE_URL:-}" ]; then
    confluence_bg=$(curl -s -u "$JIRA_USER:$JIRA_PASS" \
      "${CONFLUENCE_URL:-http://your-domain.atlassian.net/wiki:8090}/rest/api/content/$confluence_id?expand=body.storage" \
      | python3 -c "import sys,json; v=json.load(sys.stdin).get('body',{}).get('storage',{}).get('value',''); print(v)" 2>/dev/null \
      | sed 's/<[^>]*>//g' | tr '\n' ' ' | cut -c1-100)
  fi

  # 构造通知内容
  local dingtalk_content
  dingtalk_content=$(cat << DINGEOF
### 📝 需求背景

$confluence_bg

---
### 📌 需求信息

| 项目 | 内容 |
|:---|:---|
| **需求人** | 👤 $need_user |
| **Epic** | 🎯 $epic |
| **需求类型** | 📦 $req_type |
| **涉及合规** | ✅ $compliance |

---
### 🔗 文档链接

- **JIRA:** [$jira_key]($JIRA_URL/browse/$jira_key)
- **需求文档:** [Confluence]($CONFLUENCE_URL/pages/viewpage.action?pageId=$confluence_id)
DINGEOF
)

  notify_dingtalk "📋 $summary" "$dingtalk_content" "$webhook_token" "$project_type"
}

# ── 帮助 ──────────────────────────────────

show_help() {
  cat << 'HELP'
JIRA API Wrapper v2.0 (配置驱动)

用法: jira.sh <命令> [参数]

── 创建与管理 ──
  create-story    创建 Story（通用）
    --project <PROJ|MDP> --summary "标题" [其他选项]
  get-issue       <KEY>                  查看 Issue 详情
  get-confluence-url <KEY> [text|json]  从描述解析 Confluence 链接 / pageId
  append-description <KEY> '<wiki>'     追加 Wiki 块到描述（回写链接）
  search          <JQL> [max]            JQL 搜索
  get-fields      <KEY>                  查看可编辑字段
  get-transitions <KEY>                  查看可用状态转换
  transition      <KEY> <目标状态> [sprint] [hours]  状态流转
  schedule        <KEY> <Owner> <提测> <发布>         需求排期

── 查询 ──
  get-epics       [项目名]               列出 Epic
  list-projects                          列出所有项目

── 通知 ──
  notify-dingtalk <标题> <内容> [token] <type>  发送钉钉通知
  notify-story    <KEY> [pageId] [aai|mdp]     从 JIRA 读取并通知

示例:
  # 创建 PROJ Story（使用默认值）
  jira.sh create-story --project PROJ --summary "【模块B】新功能" \
    --need-user <requester-username> --background "提升效率"

  # 创建 MDP Story
  jira.sh create-story --project MDP --summary "【主数据】XX管理" \
    --need-user qishunmin --center-source "产品研发中心"

  # 状态变更
  jira.sh transition PROJ-2466 已完成
  jira.sh transition MDP-82 已评审 902 8

  # 排期
  jira.sh schedule PROJ-123 wangkang 2026-05-08 2026-05-14

  # 搜索我的 Story
  jira.sh search "project=PROJ AND assignee=currentuser()"

  # 发送通知
  jira.sh notify-story PROJ-2466 131429035 aai

配置:
  凭据（域账号优先）: JIRA_USERNAME / JIRA_PASSWORD，或 .env 中的 JIRA_USER / JIRA_PASS
  项目: config.yaml 中的 projects 节点
HELP
}

# ── 主入口 ────────────────────────────────

case "${1:-help}" in
  create-story)       shift; create_story "$@" ;;
  get-issue)          get_issue "${2:-}" ;;
  get-confluence-url) get_confluence_url "${2:-}" "${3:-text}" ;;
  search)             search_issues "${2:-}" "${3:-20}" ;;
  get-fields)         get_fields "${2:-}" ;;
  get-transitions)    get_transitions "${2:-}" ;;
  transition)         transition "${2:-}" "${3:-}" "${4:-}" "${5:-}" ;;
  schedule)           schedule "${2:-}" "${3:-}" "${4:-}" "${5:-}" ;;
  append-description) append_description "${2:-}" "${3:-}" ;;
  get-epics)          get_epics "${2:-Angelalign Intellect}" ;;
  list-projects)      list_projects ;;
  notify-dingtalk)    notify_dingtalk "${2:-}" "${3:-}" "${4:-}" "${5:-}" ;;
  notify-story)       notify_story "${2:-}" "${3:-}" "${4:-}" ;;
  help|--help|-h)     show_help ;;
  *)
    echo "未知命令: ${1:-}"
    echo "运行 '$0 help' 查看帮助"
    exit 1
    ;;
esac
