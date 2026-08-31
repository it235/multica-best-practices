#!/bin/bash
set -euo pipefail

usage() {
  echo "Usage: $0 --issue-id ID --input PRD.md [--root artifacts]" >&2
  exit 2
}

ISSUE_ID=""
INPUT=""
ROOT="artifacts"

while [ "$#" -gt 0 ]; do
  case "$1" in
    --issue-id) ISSUE_ID="${2:-}"; shift 2 ;;
    --input) INPUT="${2:-}"; shift 2 ;;
    --root) ROOT="${2:-}"; shift 2 ;;
    *) usage ;;
  esac
done

[[ "$ISSUE_ID" =~ ^[A-Za-z0-9._-]+$ ]] || usage
[ -f "$INPUT" ] || usage
[[ "$ROOT" != /* && "$ROOT" != *".."* ]] || usage

DEST_DIR="${ROOT%/}/${ISSUE_ID}"
DEST_FILE="$DEST_DIR/prd.md"
mkdir -p "$DEST_DIR"

if [ "$INPUT" != "$DEST_FILE" ]; then
  cp "$INPUT" "$DEST_FILE"
fi

printf '%s\n' "$DEST_FILE"
