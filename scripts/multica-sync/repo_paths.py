#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Resolve the templates tree for every sync script.

This repo keeps templates per language (`templates/zh_CN`, `templates/en_US`),
while some forks use a flat `templates/agents` + `templates/skills` layout.
One resolver keeps both working:

  1. `MULTICA_TEMPLATES_DIR` — explicit override (absolute, or relative to repo root)
  2. `templates/<lang>`      — lang = `MULTICA_TEMPLATE_LANG`, default `zh_CN`
  3. `templates/`            — flat-layout fallback

Only *path* resolution lives here. No host, token, workspace or ID is ever
baked in — those come from env vars or the git-ignored `config.local.json`.
"""

from __future__ import annotations

import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_LANG = "zh_CN"
_LANG_FALLBACKS = ("zh_CN", "en_US")


def _looks_like_templates(path: Path) -> bool:
    return (path / "agents").is_dir() or (path / "skills").is_dir()


def resolve_templates_root(override: str | None = None, lang: str | None = None) -> Path:
    if override:
        candidate = Path(override).expanduser()
        if not candidate.is_absolute():
            candidate = (REPO_ROOT / candidate).resolve()
        if not candidate.is_dir():
            raise ValueError(f"templates dir not found: {candidate}")
        return candidate

    env_dir = os.environ.get("MULTICA_TEMPLATES_DIR", "").strip()
    if env_dir:
        return resolve_templates_root(env_dir)

    wanted = (lang or os.environ.get("MULTICA_TEMPLATE_LANG") or DEFAULT_LANG).strip()
    for name in [wanted] + [x for x in _LANG_FALLBACKS if x != wanted]:
        candidate = REPO_ROOT / "templates" / name
        if _looks_like_templates(candidate):
            return candidate

    flat = REPO_ROOT / "templates"
    if _looks_like_templates(flat):
        return flat
    raise ValueError(f"no templates tree found under {REPO_ROOT / 'templates'}")


def agents_dir(override: str | None = None, lang: str | None = None) -> Path:
    return resolve_templates_root(override, lang) / "agents"


def skills_dir(override: str | None = None, lang: str | None = None) -> Path:
    return resolve_templates_root(override, lang) / "skills"


def squad_dir(override: str | None = None, lang: str | None = None) -> Path:
    return resolve_templates_root(override, lang) / "squad"


def resolve_template_file(value: str, override: str | None = None, lang: str | None = None) -> Path:
    """Resolve a path from config: absolute, repo-relative (`templates/...`), or templates-relative."""
    path = Path(value)
    if path.is_absolute():
        return path
    if path.parts and path.parts[0] == "templates":
        return REPO_ROOT / path
    return resolve_templates_root(override, lang) / path
