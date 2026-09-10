"""Discover Jenkins job parameters via API and resolve values from hints."""
from __future__ import annotations

import re
from typing import Any

from lib.jenkins_client import JenkinsClient, JenkinsError, parse_deploy_version

# Name matching (case-insensitive)
BRANCH_KEYS = frozenset(
    {"branchname", "branch", "gitbranch", "git_branch", "scmbranch", "branches", "git_branch_name"}
)
ENV_KEYS = frozenset({"env", "environment", "deployenv", "deploy_env", "targetenv"})
SERVICE_KEYS = frozenset({"project", "service", "module", "app", "application", "component"})
DEPLOY_VERSION_KEYS = frozenset({"deployversion", "version", "imageversion", "releaseversion"})


def _norm(name: str) -> str:
    return re.sub(r"[^a-z0-9]", "", name.lower())


def _default_value(defn: dict[str, Any]) -> str | None:
    dpv = defn.get("defaultParameterValue")
    if isinstance(dpv, dict):
        val = dpv.get("value")
        if val is not None and str(val) != "":
            return str(val)
    return None


def _param_type(defn: dict[str, Any]) -> str:
    cls = defn.get("_class") or defn.get("type") or ""
    if "Boolean" in cls:
        return "boolean"
    if "Choice" in cls:
        return "choice"
    return "string"


def _choices(defn: dict[str, Any]) -> list[str]:
    raw = defn.get("choices") or []
    return [str(c) for c in raw]


def _norm_match(norm: str, keys: frozenset[str]) -> bool:
    if norm in keys:
        return True
    return any(norm.endswith(k) or norm.startswith(k) for k in keys)


class ParameterDiscovery:
    def __init__(self, client: JenkinsClient) -> None:
        self.client = client

    def discover(
        self,
        job_path: str,
        *,
        branch: str = "",
        env: str = "",
        service: str = "",
        issue_key: str = "",
        overrides: dict[str, str] | None = None,
        use_last_success: bool = True,
    ) -> dict[str, Any]:
        overrides = overrides or {}
        definitions = self.client.get_parameter_definitions(job_path)
        parameterized = bool(definitions)

        if not parameterized:
            return {
                "job_path": job_path,
                "parameterized": False,
                "parameters": [],
                "resolved": {},
                "missing": [],
                "ready": True,
                "last_success": None,
            }

        last_build = None
        last_params: dict[str, str] = {}
        if use_last_success:
            last_build = self.client.get_last_successful_build(job_path)
            if last_build:
                last_params = self.client.get_last_successful_build_params(job_path)

        resolved: dict[str, str] = {}
        rows: list[dict[str, Any]] = []
        missing: list[str] = []

        for defn in definitions:
            name = defn.get("name") or ""
            if not name:
                continue
            norm = _norm(name)
            default = _default_value(defn)
            value: str | None = None
            source = ""

            # Priority: override > branch hint (only branch keys) > last SUCCESS > jenkins default > heuristics
            if name in overrides:
                value = overrides[name]
                source = "override"
            elif _norm_match(norm, BRANCH_KEYS) and branch:
                value = branch
                source = "hint:branch"
            elif name in last_params:
                value = last_params[name]
                source = "last_success"
            elif default is not None:
                value = default
                source = "jenkins_default"
            elif _norm_match(norm, ENV_KEYS) and env:
                value = env
                source = "hint:env"
            elif _norm_match(norm, SERVICE_KEYS) and service:
                value = service
                source = "hint:service"
            elif norm == "token" and env in ("dev", "sit"):
                value = "QA"
                source = "heuristic:token"

            ptype = _param_type(defn)
            choices = _choices(defn)
            is_missing = value is None or value == ""

            row: dict[str, Any] = {
                "name": name,
                "type": ptype,
                "description": (defn.get("description") or "").strip(),
                "default": default,
                "last_success_value": last_params.get(name),
                "choices": choices if choices else None,
                "resolved": value,
                "source": source or None,
                "missing": is_missing,
            }
            rows.append(row)

            if is_missing:
                missing.append(name)
            else:
                resolved[name] = value

        last_success_meta = None
        if last_build:
            display = last_build.get("displayName") or last_build.get("fullDisplayName") or ""
            last_success_meta = {
                "number": last_build.get("number"),
                "url": last_build.get("url"),
                "displayName": display,
                "deployVersion": parse_deploy_version(display),
                "params": last_params,
            }

        return {
            "job_path": job_path,
            "parameterized": True,
            "parameters": rows,
            "resolved": resolved,
            "missing": missing,
            "ready": len(missing) == 0,
            "last_success": last_success_meta,
            "hints": {
                "branch": branch or None,
                "env": env or None,
                "service": service or None,
                "issue_key": issue_key or None,
                "use_last_success": use_last_success,
            },
        }


def resolve_trigger_params(
    client: JenkinsClient,
    job_path: str,
    *,
    branch: str = "",
    env: str = "",
    service: str = "",
    overrides: dict[str, str] | None = None,
    strict: bool = True,
    use_last_success: bool = True,
) -> dict[str, str]:
    discovery = ParameterDiscovery(client).discover(
        job_path,
        branch=branch,
        env=env,
        service=service,
        overrides=overrides,
        use_last_success=use_last_success,
    )
    if not discovery["parameterized"]:
        return {}
    if strict and not discovery["ready"]:
        missing = ", ".join(discovery["missing"])
        raise JenkinsError(
            f"Job {job_path} missing required parameters: {missing}. "
            f"Run discover-params --json and supply --param name=value"
        )
    return dict(discovery["resolved"])
