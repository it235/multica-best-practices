"""Resolve platform skill directories for orchestrator scripts."""
from __future__ import annotations

import sys
from pathlib import Path

_LIB = Path(__file__).resolve().parents[3] / "_lib"
sys.path.insert(0, str(_LIB))
from 按 skill 名 import resolve_skill_dir  # noqa: E402

__all__ = ["resolve_skill_dir"]
