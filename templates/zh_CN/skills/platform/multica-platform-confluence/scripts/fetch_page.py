#!/usr/bin/env python3
"""Fetch a Confluence page to local Markdown (for Agent read path)."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin

import requests
import yaml
from requests.auth import HTTPBasicAuth

SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
sys.path.insert(0, str(SCRIPT_DIR / "lib"))

from html_to_md import HTMLToMarkdownConverter  # noqa: E402


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
            "ERROR: missing credentials. Set JIRA_USERNAME / JIRA_PASSWORD or CONFLUENCE_USER/PASS",
            file=sys.stderr,
        )
        sys.exit(2)
    return user, password


def api_prefix(base_url: str) -> str:
    return "/wiki/rest/api" if "atlassian.net" in base_url else "/rest/api"


def sanitize_filename(name: str) -> str:
    for char in '<>:"/\\|?*':
        name = name.replace(char, "_")
    return re.sub(r"_+", "_", name.strip("_"))[:100] or "untitled"


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch Confluence page as Markdown")
    parser.add_argument("page_id", help="Confluence page ID")
    parser.add_argument(
        "--output-dir",
        help="Output directory (default: docs/requirements/<jira_key>/ or docs/requirements/<page_id>/)",
    )
    parser.add_argument("--jira-key", help="JIRA key for output folder name")
    parser.add_argument("--json", action="store_true", help="Print JSON result")
    args = parser.parse_args()

    cfg = load_config()
    conf = cfg.get("confluence") or {}
    base_url = os.environ.get("CONFLUENCE_URL") or conf.get("url") or ""
    if not base_url:
        print("ERROR: confluence.url not configured", file=sys.stderr)
        sys.exit(2)

    user, password = resolve_credentials()
    session = requests.Session()
    session.auth = HTTPBasicAuth(user, password)
    session.headers.update({"Accept": "application/json"})

    prefix = api_prefix(base_url)
    url = urljoin(base_url.rstrip("/") + "/", f"{prefix.lstrip('/')}/content/{args.page_id}")
    resp = session.get(url, params={"expand": "body.storage,space,version"}, timeout=60)
    resp.raise_for_status()
    page = resp.json()

    storage = page.get("body", {}).get("storage", {}).get("value", "")
    converter = HTMLToMarkdownConverter()
    markdown = converter.convert(storage)

    jira_key = args.jira_key or ""
    default_root = (cfg.get("local_paths") or {}).get("requirements_dir", "docs/requirements")
    if args.output_dir:
        out_dir = Path(args.output_dir)
    elif jira_key:
        out_dir = Path(default_root) / jira_key
    else:
        out_dir = Path(default_root) / args.page_id

    out_dir.mkdir(parents=True, exist_ok=True)
    title = page.get("title", args.page_id)
    filename = sanitize_filename(title) + ".md"
    filepath = out_dir / filename

    links = page.get("_links") or {}
    page_url = f"{links.get('base', base_url.rstrip('/'))}{links.get('webui', '')}" if links.get("webui") else (
        f"{base_url.rstrip('/')}/pages/viewpage.action?pageId={page.get('id', args.page_id)}"
    )

    meta = (
        "---\n"
        f'title: "{title}"\n'
        f'confluence_id: "{page.get("id", "")}"\n'
        f'space: "{page.get("space", {}).get("key", "")}"\n'
        f"version: {page.get('version', {}).get('number', 0)}\n"
        f'url: "{page_url}"\n'
        f'jira_key: "{jira_key}"\n'
        f'downloaded_at: "{datetime.now().isoformat()}"\n'
        "---\n\n"
    )
    filepath.write_text(meta + markdown, encoding="utf-8")

    result = {
        "page_id": page.get("id"),
        "title": title,
        "url": page_url,
        "file": str(filepath),
        "jira_key": jira_key,
    }
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"OK file={filepath}")
        print(f"URL {page_url}")


if __name__ == "__main__":
    main()
