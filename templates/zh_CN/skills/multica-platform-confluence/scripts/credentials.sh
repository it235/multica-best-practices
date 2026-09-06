#!/bin/bash
# Shared credential resolution for multica platform skills
#
# Priority (highest first):
#   1. JIRA_USERNAME / JIRA_PASSWORD
#   2. JIRA_USERNAME / JIRA_PASSWORD (dev-workflow compatible)
#   3. JIRA_USER / JIRA_PASS, CONFLUENCE_USER / CONFLUENCE_PASS

load_skill_env() {
  local skill_dir="$1"
  if [ -f "$skill_dir/.env" ]; then
    set -a
    # shellcheck disable=SC1091
    . "$skill_dir/.env"
    set +a
  fi
}

resolve_credentials() {
  JIRA_USER="${JIRA_USERNAME:-${JIRA_USERNAME:-${JIRA_USER:-}}}"
  JIRA_PASS="${JIRA_PASSWORD:-${JIRA_PASSWORD:-${JIRA_PASS:-}}}"
  CONFLUENCE_USER="${JIRA_USERNAME:-${JIRA_USERNAME:-${CONFLUENCE_USER:-${JIRA_USER:-}}}}"
  CONFLUENCE_PASS="${JIRA_PASSWORD:-${JIRA_PASSWORD:-${CONFLUENCE_PASS:-${JIRA_PASS:-}}}}"
  export JIRA_USER JIRA_PASS CONFLUENCE_USER CONFLUENCE_PASS
}
