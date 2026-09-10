"""Load jobs catalog and resolve service → Jenkins job name."""
from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


def load_jobs_catalog(skill_dir: Path) -> dict[str, Any]:
    path = skill_dir / "jobs-catalog.yaml"
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def list_services(catalog: dict[str, Any], env: str) -> list[str]:
    services = catalog.get("services") or {}
    out: list[str] = []
    for key, mapping in services.items():
        if isinstance(mapping, dict) and mapping.get(env):
            out.append(key)
    return sorted(out)


def resolve_job_name(catalog: dict[str, Any], env: str, service: str) -> str:
    services = catalog.get("services") or {}
    mapping = services.get(service)
    if not mapping or not isinstance(mapping, dict):
        raise KeyError(f"Unknown service '{service}'")
    job = mapping.get(env)
    if not job:
        raise KeyError(f"Service '{service}' has no job for env '{env}'")
    return str(job)


def job_api_path(job_name: str) -> str:
    from urllib.parse import quote

    # Jenkins: /job/{name} — encode special chars e.g. <jenkins-job-name>(废弃)
    return f"/job/{quote(job_name, safe='')}"
