#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Shared Multica API client for template sync scripts."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

# No host is baked in on purpose — keep this repo shareable. Supply the base URL
# through --url, MULTICA_API_URL, or a git-ignored config.local.json.
DEFAULT_BASE_URL = ""
CONFIG_FILE = Path(__file__).resolve().parent / "config.local.json"
TIMEOUT = 120


class MulticaError(Exception):
    """API call failed."""


def load_local_config() -> dict:
    """Read the optional git-ignored config.local.json. Never commit real values."""
    try:
        if CONFIG_FILE.is_file():
            data = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
            return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        pass
    return {}


def resolve_base_url(base_url: str | None = None) -> str:
    """Resolve API base URL: --url > MULTICA_API_URL > config.local.json."""
    url = (base_url or os.environ.get("MULTICA_API_URL") or "").strip()
    if not url:
        url = str(load_local_config().get("base_url") or "").strip()
    if not url:
        url = DEFAULT_BASE_URL
    if not url:
        raise MulticaError(
            "Missing Multica base URL: pass --url, set MULTICA_API_URL, or create "
            f'{CONFIG_FILE.name} with {{"base_url": "https://multica.example.com"}}'
        )
    return url.rstrip("/")


class MulticaClient:
    """Minimal Multica REST client for agent / skill / squad sync."""

    def __init__(self, base_url: str, token: str = "", cookie: str = "", csrf: str = ""):
        self.base_url = base_url.rstrip("/")
        self.token = token.strip()
        self.cookie = cookie.strip()
        self.csrf = csrf.strip()
        self._headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "X-Client-Platform": "cli",
            "X-Client-Version": "multica-sync",
        }

    @classmethod
    def from_env(cls, base_url: str | None = None, *, require_auth: bool = True) -> "MulticaClient":
        url = resolve_base_url(base_url)
        token = os.environ.get("MULTICA_API_TOKEN", "")
        cookie = os.environ.get("MULTICA_COOKIE", "")
        csrf = os.environ.get("MULTICA_CSRF", "")
        if require_auth:
            if not token and not cookie:
                raise MulticaError(
                    "Missing auth: set MULTICA_API_TOKEN (recommended) or MULTICA_COOKIE + MULTICA_CSRF"
                )
            if cookie and not csrf and not token:
                raise MulticaError("Cookie auth requires MULTICA_CSRF (copy multica_csrf cookie value)")
        return cls(url, token=token, cookie=cookie, csrf=csrf)

    def _request(
        self,
        method: str,
        path: str,
        *,
        workspace: str | None = None,
        params: dict | None = None,
        body: dict | list | None = None,
    ):
        url = self.base_url + path
        if params:
            url += ("&" if "?" in url else "?") + urllib.parse.urlencode(params)

        headers = dict(self._headers)
        if workspace:
            headers["X-Workspace-Slug"] = str(workspace)
        if self.token:
            headers["Authorization"] = "Bearer " + self.token
        if self.cookie:
            headers["Cookie"] = self.cookie
        if self.csrf and method.upper() not in ("GET", "HEAD", "OPTIONS"):
            headers["X-CSRF-Token"] = self.csrf

        data = None
        if body is not None:
            data = json.dumps(body, ensure_ascii=False).encode("utf-8")

        req = urllib.request.Request(url, data=data, method=method, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
                raw = resp.read().decode("utf-8")
                if not raw:
                    return None, resp.status
                return json.loads(raw), resp.status
        except urllib.error.HTTPError as e:
            detail = ""
            try:
                detail = e.read().decode("utf-8", "replace")[:800]
            except Exception:
                pass
            hint = ""
            if e.code in (401, 403):
                hint = " (check MULTICA_API_TOKEN or MULTICA_COOKIE/MULTICA_CSRF)"
            raise MulticaError(f"HTTP {e.code} {e.reason} — {method} {url}{hint}\n{detail}") from e
        except urllib.error.URLError as e:
            raise MulticaError(f"Network error — {method} {url}: {e.reason}") from e

    # --- Agents ---
    def list_agents(self, workspace: str):
        data, _ = self._request("GET", "/api/agents", workspace=workspace)
        return data or []

    def get_agent(self, workspace: str, agent_id: str):
        data, _ = self._request("GET", f"/api/agents/{agent_id}", workspace=workspace)
        return data

    def update_agent_instructions(
        self,
        workspace: str,
        agent_id: str,
        instructions: str,
        conversation_starters: list | None = None,
    ):
        body = {
            "instructions": instructions,
            "conversation_starters": conversation_starters or [],
        }
        return self._request("PUT", f"/api/agents/{agent_id}", workspace=workspace, body=body)

    def list_agent_skills(self, workspace: str, agent_id: str):
        data, _ = self._request("GET", f"/api/agents/{agent_id}/skills", workspace=workspace)
        return data or []

    # --- Skills ---
    def list_skills(self, workspace: str):
        data, _ = self._request("GET", "/api/skills", workspace=workspace)
        return data or []

    def create_skill(self, workspace: str, payload: dict):
        return self._request("POST", "/api/skills", workspace=workspace, body=payload)

    def update_skill(self, workspace: str, skill_id: str, payload: dict):
        return self._request("PUT", f"/api/skills/{skill_id}", workspace=workspace, body=payload)

    # --- Squads ---
    def get_squad(self, workspace: str, squad_id: str):
        data, _ = self._request("GET", f"/api/squads/{squad_id}", workspace=workspace)
        return data

    def list_squad_members(self, workspace: str, squad_id: str):
        data, _ = self._request("GET", f"/api/squads/{squad_id}/members", workspace=workspace)
        return data or []

    def list_squads(self, workspace: str):
        data, _ = self._request("GET", "/api/squads", workspace=workspace)
        return data or []

    def create_squad(self, workspace: str, payload: dict):
        data, _ = self._request("POST", "/api/squads", workspace=workspace, body=payload)
        return data

    def update_squad(self, workspace: str, squad_id: str, payload: dict):
        data, _ = self._request("PUT", f"/api/squads/{squad_id}", workspace=workspace, body=payload)
        return data

    def add_squad_member(
        self,
        workspace: str,
        squad_id: str,
        member_id: str,
        role: str = "",
        member_type: str = "agent",
    ):
        body = {"member_type": member_type, "member_id": member_id}
        if role:
            body["role"] = role
        data, _ = self._request("POST", f"/api/squads/{squad_id}/members", workspace=workspace, body=body)
        return data

    # --- Runtimes (an agent cannot be created without one) ---
    def list_runtimes(self, workspace: str, owner: str = "me"):
        params = {"owner": owner} if owner else None
        data, _ = self._request("GET", "/api/runtimes", workspace=workspace, params=params)
        return data or []

    # --- Agents (create) ---
    def create_agent(self, workspace: str, payload: dict):
        data, _ = self._request("POST", "/api/agents", workspace=workspace, body=payload)
        return data

    # --- Agent <-> skill bindings ---
    def add_agent_skills(self, workspace: str, agent_id: str, skill_ids: list):
        body = {"skill_ids": list(skill_ids)}
        data, _ = self._request("POST", f"/api/agents/{agent_id}/skills/add", workspace=workspace, body=body)
        return data

    def set_agent_skills(self, workspace: str, agent_id: str, skill_ids: list):
        body = {"skill_ids": list(skill_ids)}
        data, _ = self._request("PUT", f"/api/agents/{agent_id}/skills", workspace=workspace, body=body)
        return data


def utf8_stdio():
    try:
        import sys

        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
