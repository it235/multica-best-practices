#!/usr/bin/env python3
from __future__ import annotations

import ast
from pathlib import Path

import yaml

SKILL_DIR = Path(__file__).resolve().parent.parent
for rel in ["SKILL.md", "config.yaml", "scripts/trigger_cicd.py", "scripts/按 skill 名.py"]:
    assert (SKILL_DIR / rel).is_file(), rel

ast.parse((SKILL_DIR / "scripts/trigger_cicd.py").read_text(encoding="utf-8"))
meta = yaml.safe_load(SKILL_DIR.joinpath("SKILL.md").read_text(encoding="utf-8").split("---", 2)[1])
assert meta.get("name") == "multica-artifact-cicd-sync"
print("validation ok")
