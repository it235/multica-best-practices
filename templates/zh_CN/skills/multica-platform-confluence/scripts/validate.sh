#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SKILL_DIR="$(dirname "$SCRIPT_DIR")"
cd "$SKILL_DIR"
for f in SKILL.md config.yaml .env.example scripts/credentials.sh scripts/confluence.sh scripts/fetch_page.py scripts/publish_design.py scripts/lib/md_to_confluence.py scripts/lib/html_to_md.py scripts/lib/按 skill 名.sh; do
  [ -f "$f" ] || { echo "missing $f"; exit 1; }
done
bash -n scripts/credentials.sh
bash -n scripts/confluence.sh
python3 -m py_compile scripts/publish_design.py scripts/fetch_page.py scripts/lib/md_to_confluence.py scripts/lib/html_to_md.py
python3 -c "
import yaml, sys
from pathlib import Path
text = Path('SKILL.md').read_text(encoding='utf-8')
meta = yaml.safe_load(text.split('---', 2)[1])
assert meta.get('name') == 'multica-platform-confluence', meta.get('name')
yaml.safe_load(open('config.yaml'))
print('SKILL.md ok')
"
echo "validation ok"
