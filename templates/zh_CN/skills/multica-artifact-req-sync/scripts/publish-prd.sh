#!/bin/bash
# PRD 编排：Confluence 页面 + JIRA Story + 可选钉钉
# 依赖 multica-platform-confluence / multica-platform-jira（MULTICA_SKILLS_ROOT 或同级目录）
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SKILL_DIR="$(dirname "$SCRIPT_DIR")"
# shellcheck source=按 skill 名.sh
source "$SCRIPT_DIR/按 skill 名.sh"
CONFLUENCE_SKILL="$(resolve_skill_dir multica-platform-confluence "$SKILL_DIR")"
JIRA_SKILL="$(resolve_skill_dir multica-platform-jira "$SKILL_DIR")"

usage() {
  echo "Usage: $0 --project KEY --summary TITLE --html-file FILE [jira options passed to create-story]"
  exit 1
}

PROJECT="" SUMMARY="" HTML_FILE=""
JIRA_ARGS=()

while [ $# -gt 0 ]; do
  case "$1" in
    --project) PROJECT="$2"; shift 2 ;;
    --summary) SUMMARY="$2"; shift 2 ;;
    --html-file) HTML_FILE="$2"; shift 2 ;;
    --) shift; JIRA_ARGS+=("$@"); break ;;
    *) JIRA_ARGS+=("$1"); shift ;;
  esac
done

[ -n "$PROJECT" ] && [ -n "$SUMMARY" ] && [ -f "$HTML_FILE" ] || usage

PARENT=$(python3 -c "import yaml; c=yaml.safe_load(open('$CONFLUENCE_SKILL/config.yaml')); print(c['confluence']['default_parent_page_id'])")
SPACE=$(python3 -c "import yaml; c=yaml.safe_load(open('$CONFLUENCE_SKILL/config.yaml')); print(c['confluence']['default_space'])")
HTML=$(cat "$HTML_FILE")

PAGE_JSON=$(bash "$CONFLUENCE_SKILL/scripts/confluence.sh" create-page "$SUMMARY" "$PARENT" "$HTML" "$SPACE")
PAGE_ID=$(echo "$PAGE_JSON" | python3 -c "import sys,json; print(json.load(sys.stdin).get('id',''))" 2>/dev/null || true)
PAGE_URL=$(echo "$PAGE_JSON" | python3 -c "
import sys,json
d=json.load(sys.stdin)
links=d.get('_links',{})
base=links.get('base','').rstrip('/')
web=links.get('webui','')
print(base+web if web else '')
" 2>/dev/null || true)

DESC="h1. Requirement Document\n\nConfluence: ${PAGE_URL}\n"
JIRA_OUT=$(bash "$JIRA_SKILL/scripts/jira.sh" create-story --project "$PROJECT" --summary "$SUMMARY" --description "$DESC" "${JIRA_ARGS[@]}")
echo "$JIRA_OUT"
echo "Confluence: $PAGE_URL"
echo "PageId: $PAGE_ID"
