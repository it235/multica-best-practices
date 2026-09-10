"""JIRA read/write helpers (stdlib only, cross-platform)."""

from __future__ import annotations

import base64
import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

import yaml


def _skill_dir() -> Path:
    return Path(__file__).resolve().parent.parent.parent


def load_config() -> dict:
    with open(_skill_dir() / "config.yaml", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def resolve_credentials() -> tuple[str, str]:
    user = (
        os.environ.get("JIRA_USERNAME")
        or os.environ.get("JIRA_USERNAME")
        or os.environ.get("JIRA_USER")
        or ""
    )
    password = (
        os.environ.get("JIRA_PASSWORD")
        or os.environ.get("JIRA_PASSWORD")
        or os.environ.get("JIRA_PASS")
        or ""
    )
    if not user or not password:
        print(
            "ERROR: missing credentials. Set JIRA_USERNAME/PASSWORD or JIRA_USER/JIRA_PASS",
            file=sys.stderr,
        )
        sys.exit(2)
    return user, password


def jira_base_url(cfg: dict | None = None) -> str:
    cfg = cfg or load_config()
    return (
        os.environ.get("JIRA_URL")
        or (cfg.get("jira") or {}).get("url")
        or "http://your-domain.atlassian.net:8080"
    ).rstrip("/")


def _request(
    method: str,
    path: str,
    *,
    payload: dict | None = None,
    cfg: dict | None = None,
) -> Any:
    user, password = resolve_credentials()
    base = jira_base_url(cfg)
    url = f"{base}{path}"
    headers = {
        "Authorization": f"Basic {base64.b64encode(f'{user}:{password}'.encode()).decode()}",
        "Accept": "application/json",
    }
    data = None
    if payload is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(payload).encode()
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = resp.read()
            return json.loads(body) if body else {}
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode(errors="replace")
        print(f"ERROR: JIRA {method} {path} failed ({exc.code}): {detail}", file=sys.stderr)
        sys.exit(exc.code if exc.code < 500 else 1)


def get_issue_description(issue_key: str, cfg: dict | None = None) -> str:
    issue = _request("GET", f"/rest/api/2/issue/{issue_key}?fields=description", cfg=cfg)
    return (issue.get("fields") or {}).get("description") or ""


def get_confluence_links(issue_key: str, cfg: dict | None = None) -> dict:
    """Return Confluence URLs and pageIds parsed from JIRA issue description + remote links."""
    desc = get_issue_description(issue_key, cfg)

    urls = re.findall(r"https?://[^\s\]|]+confluence[^\s\]|>]+", desc, re.I)
    urls += re.findall(r"https?://[^\s\]|]+/pages/viewpage\.action\?pageId=\d+", desc, re.I)
    page_ids = re.findall(r"pageId=(\d+)", desc, re.I)

    try:
        links = _request("GET", f"/rest/api/2/issue/{issue_key}/remotelink", cfg=cfg)
        for item in links if isinstance(links, list) else []:
            url = (item.get("object") or {}).get("url") or ""
            if "confluence" in url.lower() or "pageId=" in url:
                urls.append(url)
                match = re.search(r"pageId=(\d+)", url)
                if match:
                    page_ids.append(match.group(1))
    except SystemExit:
        pass

    urls = list(dict.fromkeys(urls))
    page_ids = list(dict.fromkeys(page_ids))
    return {"issue_key": issue_key, "urls": urls, "page_ids": page_ids}


def resolve_requirement_parent_page_id(
    issue_key: str, cfg: dict | None = None, *, required: bool = True
) -> str | None:
    """First Confluence pageId in JIRA = PRD/requirements hub; used as artifact parent."""
    links = get_confluence_links(issue_key, cfg)
    if links["page_ids"]:
        return links["page_ids"][0]
    if required:
        print(
            f"ERROR: no Confluence link in JIRA {issue_key}. "
            "Add PRD page link to issue description, or pass --parent / use config fallback.",
            file=sys.stderr,
        )
        sys.exit(1)
    return None


def append_description(issue_key: str, wiki_block: str, cfg: dict | None = None) -> None:
    desc = get_issue_description(issue_key, cfg)
    _request(
        "PUT",
        f"/rest/api/2/issue/{issue_key}",
        payload={"fields": {"description": desc + wiki_block}},
        cfg=cfg,
    )


def append_artifact_link(
    issue_key: str,
    *,
    section: str,
    title: str,
    url: str,
    source_file: str = "",
    cfg: dict | None = None,
) -> None:
    source_line = f"\n* _Auto-published from: {source_file}_" if source_file else ""
    wiki = f"h3. {section}\n* [{title}|{url}]{source_line}\n"
    append_description(issue_key, wiki, cfg=cfg)
