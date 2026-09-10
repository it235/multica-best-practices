#!/usr/bin/env python3
from __future__ import annotations

import ast
import sys
from pathlib import Path

import yaml

SKILL_DIR = Path(__file__).resolve().parent.parent
_LIB = SKILL_DIR.parent.parent / "_lib"
if str(_LIB) not in sys.path:
    sys.path.insert(0, str(_LIB))

from 按 skill 名 import resolve_skill_dir  # noqa: E402

for rel in ["SKILL.md", "config.yaml"]:
    assert (SKILL_DIR / rel).is_file(), rel

platform_apifox = resolve_skill_dir("multica-platform-apifox", SKILL_DIR)
run_apifox = platform_apifox / "scripts" / "run_apifox.py"
assert run_apifox.is_file(), f"platform run_apifox missing: {run_apifox}"

ast.parse(run_apifox.read_text(encoding="utf-8"))
meta = yaml.safe_load(SKILL_DIR.joinpath("SKILL.md").read_text(encoding="utf-8").split("---", 2)[1])
assert meta.get("name") == "multica-test-t3-api-automation"
print("validation ok")
