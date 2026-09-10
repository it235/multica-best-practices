#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SKILL_DIR="$(dirname "$SCRIPT_DIR")"
cd "$SKILL_DIR"
for f in SKILL.md config.yaml .env.example scripts/credentials.sh scripts/jira.sh; do
  [ -f "$f" ] || { echo "missing $f"; exit 1; }
done
bash -n scripts/credentials.sh
bash -n scripts/jira.sh
python3 -c "
import yaml
from pathlib import Path
text = Path('SKILL.md').read_text(encoding='utf-8')
meta = yaml.safe_load(text.split('---', 2)[1])
assert meta.get('name') == 'multica-platform-jira', meta.get('name')
c = yaml.safe_load(open('config.yaml'))
assert 'jira' in c and 'projects' in c
print('validation ok')
"
