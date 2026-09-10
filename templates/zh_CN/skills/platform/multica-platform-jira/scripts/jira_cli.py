#!/usr/bin/env python3
"""Cross-platform JIRA CLI (Windows / macOS / Linux). Prefer over bash jira.sh for artifact flows."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "lib"))

from jira_client import (  # noqa: E402
    append_artifact_link,
    append_description,
    get_confluence_links,
    resolve_requirement_parent_page_id,
)

GET_ISSUE_SCRIPT = Path(__file__).resolve().parent / "get_issue.py"


def main() -> None:
    parser = argparse.ArgumentParser(description="JIRA platform CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    p_gi = sub.add_parser(
        "get-issue",
        help="Fetch issue JSON (summary, description, Confluence/Figma links, attachments)",
    )
    p_gi.add_argument("--url", required=True, help="Full JIRA issue URL")
    p_gi.add_argument("--output", "-o", help="Write JSON to file")

    p_gcu = sub.add_parser("get-confluence-url", help="Parse Confluence links from issue")
    p_gcu.add_argument("issue_key")
    p_gcu.add_argument("--json", action="store_true")

    p_parent = sub.add_parser(
        "resolve-parent-page-id",
        help="First Confluence pageId in issue (PRD hub for child artifacts)",
    )
    p_parent.add_argument("issue_key")

    p_append = sub.add_parser("append-description", help="Append Wiki block to issue description")
    p_append.add_argument("issue_key")
    p_append.add_argument("wiki_block")

    p_link = sub.add_parser("append-artifact-link", help="Append h3 + link block for an artifact")
    p_link.add_argument("issue_key")
    p_link.add_argument("--section", required=True)
    p_link.add_argument("--title", required=True)
    p_link.add_argument("--url", required=True)
    p_link.add_argument("--source", default="")

    args = parser.parse_args()

    if args.command == "get-issue":
        cmd = [sys.executable, str(GET_ISSUE_SCRIPT), "--url", args.url]
        if args.output:
            cmd.extend(["--output", args.output])
        subprocess.run(cmd, check=True)
    elif args.command == "get-confluence-url":
        result = get_confluence_links(args.issue_key)
        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            if not result["urls"] and not result["page_ids"]:
                print(f"No Confluence link found in {args.issue_key}", file=sys.stderr)
                sys.exit(1)
            for url in result["urls"]:
                print(url)
            for pid in result["page_ids"]:
                if not any(pid in u for u in result["urls"]):
                    print(f"pageId={pid}")
    elif args.command == "resolve-parent-page-id":
        print(resolve_requirement_parent_page_id(args.issue_key))
    elif args.command == "append-description":
        append_description(args.issue_key, args.wiki_block)
        print(f"OK {args.issue_key} description updated")
    elif args.command == "append-artifact-link":
        append_artifact_link(
            args.issue_key,
            section=args.section,
            title=args.title,
            url=args.url,
            source_file=args.source,
        )
        print(f"OK {args.issue_key} artifact link appended")


if __name__ == "__main__":
    main()
