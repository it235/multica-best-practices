#!/bin/bash
# 设计文档编排：Confluence publish + JIRA append-description
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SKILL_DIR="$(dirname "$SCRIPT_DIR")"
# shellcheck source=按 skill 名.sh
source "$SCRIPT_DIR/按 skill 名.sh"
CONFLUENCE_SKILL="$(resolve_skill_dir multica-platform-confluence "$SKILL_DIR")"
JIRA_SKILL="$(resolve_skill_dir multica-platform-jira "$SKILL_DIR")"

ISSUE_KEY="${1:-}"
MD_FILE="${2:-}"
[ -n "$ISSUE_KEY" ] && [ -f "$MD_FILE" ] || {
  echo "Usage: $0 <ISSUE-KEY> <path-to-design.md>"
  exit 1
}

pip install -q -r "$CONFLUENCE_SKILL/scripts/requirements.txt" 2>/dev/null || true

RESULT=$(python "$CONFLUENCE_SKILL/scripts/publish_design.py" "$ISSUE_KEY" "$MD_FILE" --json)
URL=$(echo "$RESULT" | python3 -c "import sys,json; print(json.load(sys.stdin)['url'])")
TITLE=$(echo "$RESULT" | python3 -c "import sys,json; print(json.load(sys.stdin)['title'])")

WIKI=$'h3. 设计文档 (Design Document)\n* ['"$TITLE"$'|'"$URL"$']\n* _Auto-published from: '"$(basename "$MD_FILE")"$'_\n'
bash "$JIRA_SKILL/scripts/jira.sh" append-description "$ISSUE_KEY" "$WIKI"

echo "Confluence: $URL"
echo "JIRA: $ISSUE_KEY updated"
