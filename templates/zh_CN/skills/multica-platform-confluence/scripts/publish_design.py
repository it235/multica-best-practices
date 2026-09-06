#!/usr/bin/env python3
"""Publish a Markdown design doc to Confluence (upsert by title)."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from urllib.parse import urljoin

import requests
import yaml
from requests.auth import HTTPBasicAuth

SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
sys.path.insert(0, str(SCRIPT_DIR / "lib"))

from md_to_confluence import MarkdownToConfluenceConverter  # noqa: E402


def jira_lib_dir() -> Path:
    root = os.environ.get("MULTICA_SKILLS_ROOT")
    if root:
        candidate = Path(root) / "multica-platform-jira" / "scripts" / "lib"
        if candidate.is_dir():
            return candidate
    sibling = SKILL_DIR.parent / "multica-platform-jira" / "scripts" / "lib"
    if sibling.is_dir():
        return sibling
    print(
        "ERROR: cannot locate multica-platform-jira/scripts/lib. "
        "Set MULTICA_SKILLS_ROOT or co-locate platform skills.",
        file=sys.stderr,
    )
    sys.exit(2)


def resolve_parent_page_id(
    issue_key: str,
    explicit_parent: str | None,
    no_parent_from_jira: bool,
    project_cfg: dict,
    conf: dict,
) -> str | None:
    if explicit_parent:
        return explicit_parent
    if not no_parent_from_jira:
        sys.path.insert(0, str(jira_lib_dir()))
        from jira_client import resolve_requirement_parent_page_id  # noqa: E402

        parent = resolve_requirement_parent_page_id(issue_key, required=False)
        if parent:
            return parent
    return (
        project_cfg.get("design_parent_page_id")
        or conf.get("design_parent_page_id")
        or conf.get("default_parent_page_id")
    )


def load_config() -> dict:
    with open(SKILL_DIR / "config.yaml", encoding="utf-8") as f:
        return yaml.safe_load(f)


def resolve_credentials() -> tuple[str, str]:
    user = (
        os.environ.get("JIRA_USERNAME")
        or os.environ.get("JIRA_USERNAME")
        or os.environ.get("CONFLUENCE_USER")
        or os.environ.get("JIRA_USER")
        or ""
    )
    password = (
        os.environ.get("JIRA_PASSWORD")
        or os.environ.get("JIRA_PASSWORD")
        or os.environ.get("CONFLUENCE_PASS")
        or os.environ.get("JIRA_PASS")
        or ""
    )
    if not user or not password:
        print(
            "ERROR: missing credentials. Set JIRA_USERNAME/PASSWORD "
            "or CONFLUENCE_USER/CONFLUENCE_PASS",
            file=sys.stderr,
        )
        sys.exit(2)
    return user, password


def project_prefix(issue_key: str) -> str:
    return issue_key.split("-", 1)[0].upper()


def resolve_project(cfg: dict, issue_key: str) -> dict:
    projects = cfg.get("projects") or {}
    prefix = project_prefix(issue_key)
    merged = dict(projects.get("default") or {})
    merged.update(projects.get(prefix) or {})
    return merged


def api_prefix(base_url: str) -> str:
    return "/wiki/rest/api" if "atlassian.net" in base_url else "/rest/api"


def find_page(session: requests.Session, base_url: str, space: str, title: str) -> dict | None:
    prefix = api_prefix(base_url)
    cql = f'space = "{space}" AND title = "{title}" AND type = page'
    url = urljoin(base_url.rstrip("/") + "/", f"{prefix.lstrip('/')}/content/search")
    resp = session.get(url, params={"cql": cql, "limit": "1", "expand": "version"}, timeout=30)
    resp.raise_for_status()
    results = resp.json().get("results") or []
    return results[0] if results else None


def upsert_page(
    session: requests.Session,
    base_url: str,
    space: str,
    title: str,
    body: str,
    parent_id: str | None,
) -> dict:
    prefix = api_prefix(base_url)
    existing = find_page(session, base_url, space, title)
    payload = {
        "type": "page",
        "title": title,
        "body": {"storage": {"value": body, "representation": "storage"}},
    }
    if existing:
        page_id = existing["id"]
        version = existing.get("version", {}).get("number", 1)
        payload["id"] = page_id
        payload["version"] = {"number": version + 1}
        url = urljoin(base_url.rstrip("/") + "/", f"{prefix.lstrip('/')}/content/{page_id}")
        resp = session.put(url, json=payload, timeout=30)
    else:
        payload["space"] = {"key": space}
        if parent_id:
            payload["ancestors"] = [{"id": str(parent_id)}]
        url = urljoin(base_url.rstrip("/") + "/", f"{prefix.lstrip('/')}/content")
        resp = session.post(url, json=payload, timeout=30)
    resp.raise_for_status()
    return resp.json()


def page_url(base_url: str, page: dict) -> str:
    links = page.get("_links") or {}
    if links.get("webui"):
        return f"{links.get('base', base_url.rstrip('/'))}{links['webui']}"
    return f"{base_url.rstrip('/')}/pages/viewpage.action?pageId={page.get('id', '')}"


def main() -> None:
    parser = argparse.ArgumentParser(description="Publish design Markdown to Confluence")
    parser.add_argument("issue_key", help="JIRA issue key, e.g. PROJ-1813")
    parser.add_argument("md_file", help="Path to design Markdown file")
    parser.add_argument("--space", help="Confluence space key override")
    parser.add_argument("--parent", help="Parent page ID override")
    parser.add_argument(
        "--no-parent-from-jira",
        action="store_true",
        help="Do not resolve parent from JIRA Confluence link; use config fallback only",
    )
    parser.add_argument(
        "--append-jira",
        action="store_true",
        help="Append published page link to JIRA issue description",
    )
    parser.add_argument("--title", help="Page title override")
    parser.add_argument("--json", action="store_true", help="Print JSON result")
    args = parser.parse_args()

    md_path = Path(args.md_file)
    if not md_path.exists():
        print(f"ERROR: file not found: {md_path}", file=sys.stderr)
        sys.exit(1)

    cfg = load_config()
    conf = cfg.get("confluence") or {}
    base_url = os.environ.get("CONFLUENCE_URL") or conf.get("url") or ""
    if not base_url:
        print("ERROR: confluence.url not configured", file=sys.stderr)
        sys.exit(2)

    project_cfg = resolve_project(cfg, args.issue_key)
    space = args.space or project_cfg.get("confluence_space") or conf.get("default_space")
    parent_id = resolve_parent_page_id(
        args.issue_key,
        args.parent,
        args.no_parent_from_jira,
        project_cfg,
        conf,
    )
    if not parent_id:
        print(
            "ERROR: no parent page ID. JIRA issue needs a Confluence PRD link, "
            "or pass --parent / configure design_parent_page_id fallback.",
            file=sys.stderr,
        )
        sys.exit(2)
    if not space:
        print("ERROR: no Confluence space configured", file=sys.stderr)
        sys.exit(2)

    content = md_path.read_text(encoding="utf-8")
    converter = MarkdownToConfluenceConverter()
    title, body = converter.convert(content, title_override=args.title)
    if not title.endswith("[AI]"):
        title = f"{title} [AI]"

    user, password = resolve_credentials()
    session = requests.Session()
    session.auth = HTTPBasicAuth(user, password)
    session.headers.update({"Accept": "application/json", "Content-Type": "application/json"})

    page = upsert_page(session, base_url, space, title, body, parent_id)
    url = page_url(base_url, page)
    if args.append_jira:
        sys.path.insert(0, str(jira_lib_dir()))
        from jira_client import append_artifact_link  # noqa: E402

        append_artifact_link(
            args.issue_key,
            section="设计文档 (Design Document)",
            title=title,
            url=url,
            source_file=md_path.name,
        )
    result = {
        "issue_key": args.issue_key,
        "page_id": page.get("id"),
        "title": title,
        "url": url,
        "space": space,
        "parent_page_id": parent_id,
        "source_file": str(md_path),
    }
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"OK page_id={page.get('id')}")
        print(f"URL {url}")


if __name__ == "__main__":
    main()
