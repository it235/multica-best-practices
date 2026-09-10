"""Load skill .env and resolve Jenkins credentials (domain account first)."""
from __future__ import annotations

import os
from pathlib import Path


def load_skill_env(skill_dir: Path) -> None:
    env_file = skill_dir / ".env"
    if not env_file.is_file():
        return
    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


def resolve_jenkins_credentials() -> tuple[str, str]:
    user = (
        os.environ.get("ATLASSIAN_USER")
        or os.environ.get("ATLASSIAN_USER")
        or os.environ.get("JENKINS_USER")
        or ""
    )
    password = (
        os.environ.get("ATLASSIAN_PASS")
        or os.environ.get("ATLASSIAN_PASS")
        or os.environ.get("JENKINS_PASSWORD")
        or ""
    )
    return user, password

