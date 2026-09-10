#!/usr/bin/env python3
from __future__ import annotations

import ast
from pathlib import Path

import yaml

SKILL_DIR = Path(__file__).resolve().parent.parent
REQUIRED = [
    "SKILL.md",
    "config.yaml",
    "jobs-catalog.yaml",
    "reference.md",
    "scripts/trigger_env.py",
    "scripts/list_jobs.py",
    "scripts/jenkins_cli.py",
    "scripts/lib/param_discovery.py",
]

for rel in REQUIRED:
    assert (SKILL_DIR / rel).is_file(), f"missing {rel}"

for py in SKILL_DIR.glob("scripts/**/*.py"):
    ast.parse(py.read_text(encoding="utf-8"), filename=str(py))

meta = yaml.safe_load(SKILL_DIR.joinpath("SKILL.md").read_text(encoding="utf-8").split("---", 2)[1])
assert meta.get("name") == "multica-platform-jenkins"
cfg = yaml.safe_load((SKILL_DIR / "config.yaml").read_text(encoding="utf-8"))
catalog = yaml.safe_load((SKILL_DIR / "jobs-catalog.yaml").read_text(encoding="utf-8"))
assert cfg["jenkins"]["base_url"] == "http://<JENKINS_URL>"
assert "environments" in cfg
assert len(catalog.get("services", {})) >= 50
print("validation ok")

