#!/usr/bin/env bash
# Offline validation for multica-artifact-req-sync (orchestrator).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SKILL_DIR="$(dirname "$SCRIPT_DIR")"
SKILLS_ROOT="$(dirname "$SKILL_DIR")"

cd "$SKILL_DIR"

fail() { echo "ERROR: $*" >&2; exit 1; }

for required in SKILL.md config.yaml .env.example scripts/credentials.sh scripts/publish-prd.sh; do
  [ -f "$required" ] || fail "missing required file: $required"
done

for platform in multica-platform-confluence multica-platform-jira; do
  [ -f "$SKILLS_ROOT/$platform/SKILL.md" ] || fail "missing platform skill: $platform"
done

bash -n scripts/credentials.sh
bash -n scripts/publish-prd.sh

python3 - <<'PY'
import pathlib, yaml, sys
root = pathlib.Path(".")
text = (root / "SKILL.md").read_text(encoding="utf-8")
if not text.startswith("---\n"):
    sys.exit("SKILL.md missing YAML frontmatter")
meta = yaml.safe_load(text.split("---", 2)[1])
if meta.get("name") != "multica-artifact-req-sync":
    sys.exit("unexpected skill name")
orch = (meta.get("metadata") or {}).get("orchestrates") or []
expected = {"multica-platform-confluence", "multica-platform-jira"}
if not expected.issubset(set(orch)):
    sys.exit(f"metadata.orchestrates must include {expected}")
print("SKILL.md ok")
PY

echo "validation ok"
