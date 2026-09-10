#!/bin/bash
# Resolve platform skill directories for orchestrator scripts.
# Priority: MULTICA_SKILLS_ROOT > sibling of caller skill dir.

resolve_skill_dir() {
  local skill_name="$1"
  local caller_skill_dir="${2:-}"

  if [ -n "${MULTICA_SKILLS_ROOT:-}" ] && [ -d "$MULTICA_SKILLS_ROOT/$skill_name" ]; then
    echo "$MULTICA_SKILLS_ROOT/$skill_name"
    return 0
  fi

  if [ -n "$caller_skill_dir" ] && [ -d "$(dirname "$caller_skill_dir")/$skill_name" ]; then
    echo "$(dirname "$caller_skill_dir")/$skill_name"
    return 0
  fi

  echo "ERROR: cannot locate skill '$skill_name'. Set MULTICA_SKILLS_ROOT or co-locate skills under templates/skills/." >&2
  return 1
}
