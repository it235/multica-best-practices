"""Load multica-platform-jenkins config.yaml."""
from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


def load_config(skill_dir: Path) -> dict[str, Any]:
    path = skill_dir / "config.yaml"
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f) or {}
