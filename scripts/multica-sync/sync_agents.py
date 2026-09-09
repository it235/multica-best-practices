#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sync templates/zh_CN/agents/*.md instructions to Multica agents (see repo_paths).

Reads each agent template markdown, extracts the ```text ... ``` block (Agent
Instructions body), and PUT /api/agents/{id} with:
  {"instructions": "...", "conversation_starters": []}

Mapping sources (pick one):
  1. --squad <uuid>   Auto-fetch GET /api/squads/{id}/members and map by role
  2. --mapping file   Manual JSON: template stem -> agent UUID or name

Auth (env):
  MULTICA_API_TOKEN          Bearer token (recommended)
  MULTICA_COOKIE + MULTICA_CSRF   Browser session fallback
  MULTICA_API_URL            Base URL; or config.local.json (no host is built in)

Examples:
  python sync_agents.py --workspace 100 --squad <squad-uuid>
  python sync_agents.py --workspace 100 --squad <squad-uuid> --dry-run
  python sync_agents.py --workspace 100 --squad ... --print-mapping
  python sync_agents.py --workspace 100 --mapping agent-mapping.json --only architect
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from multica_client import MulticaClient, MulticaError, utf8_stdio
from repo_paths import agents_dir
from squad_mapping import build_mapping_from_squad

REPO_ROOT = Path(__file__).resolve().parents[2]
AGENTS_DIR = agents_dir()
TEXT_BLOCK_RE = re.compile(r"```text\s*\n(.*?)```", re.DOTALL)


def extract_instructions(markdown: str) -> str:
    match = TEXT_BLOCK_RE.search(markdown)
    if not match:
        raise ValueError("no ```text ... ``` block found")
    return match.group(1).strip("\n")


def load_mapping(path: Path) -> dict[str, str]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("mapping must be a JSON object")
    return {str(k): str(v) for k, v in data.items()}


def resolve_agent_id(client: MulticaClient, workspace: str, target: str) -> str:
    """Return UUID when target looks like UUID, else lookup by agent name."""
    if re.fullmatch(
        r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}",
        target,
    ):
        return target
    agents = client.list_agents(workspace)
    for agent in agents:
        if agent.get("name") == target:
            return agent["id"]
    names = sorted(a.get("name", "") for a in agents)
    raise MulticaError(f"Agent name not found: {target!r}. Available: {', '.join(names)}")


def main() -> int:
    utf8_stdio()
    parser = argparse.ArgumentParser(description="Sync templates/agents to Multica agent instructions")
    parser.add_argument("--workspace", required=True, help="Workspace slug or UUID")
    src = parser.add_mutually_exclusive_group(required=True)
    src.add_argument(
        "--squad",
        help="Squad UUID — auto-build mapping from GET /api/squads/{id}/members",
    )
    src.add_argument(
        "--mapping",
        help="JSON map: template stem -> agent UUID or name",
    )
    parser.add_argument("--url", help="Multica base URL (or MULTICA_API_URL)")
    parser.add_argument("--token", help="API token (or MULTICA_API_TOKEN)")
    parser.add_argument("--dry-run", action="store_true", help="Print actions without calling API")
    parser.add_argument("--only", action="append", help="Sync only these template stems (repeatable)")
    parser.add_argument(
        "--print-mapping",
        action="store_true",
        help="Print resolved stem->agent_id JSON and exit (with --squad)",
    )
    args = parser.parse_args()

    need_auth = not args.dry_run or bool(args.squad) or bool(args.print_mapping)
    try:
        client = MulticaClient.from_env(args.url, require_auth=need_auth)
        if args.token:
            client.token = args.token
    except MulticaError as e:
        print(str(e), file=sys.stderr)
        return 1

    mapping: dict[str, str] = {}
    if args.squad:
        try:
            mapping, warnings = build_mapping_from_squad(client, args.workspace, args.squad)
            for w in warnings:
                print(f"[WARN] {w}", file=sys.stderr)
            print(f"Resolved {len(mapping)} agents from squad {args.squad}", file=sys.stderr)
        except MulticaError as e:
            print(str(e), file=sys.stderr)
            return 1
        if args.print_mapping:
            print(json.dumps(dict(sorted(mapping.items())), ensure_ascii=False, indent=2))
            return 0
    else:
        mapping_path = Path(args.mapping)
        if not mapping_path.is_file():
            print(f"Mapping file not found: {mapping_path}", file=sys.stderr)
            return 1
        mapping = load_mapping(mapping_path)

    if args.only:
        unknown = set(args.only) - set(mapping)
        if unknown:
            print(f"Unknown --only stems (not in mapping): {', '.join(sorted(unknown))}", file=sys.stderr)
            return 1
        mapping = {k: v for k, v in mapping.items() if k in args.only}

    ok, fail = 0, 0
    for stem, target in sorted(mapping.items()):
        template_path = AGENTS_DIR / f"{stem}.md"
        if not template_path.is_file():
            print(f"[SKIP] {stem}: template missing at {template_path}")
            fail += 1
            continue
        try:
            instructions = extract_instructions(template_path.read_text(encoding="utf-8"))
            agent_id = target if (args.dry_run and args.squad) else resolve_agent_id(
                client, args.workspace, target
            )
        except (ValueError, MulticaError) as e:
            print(f"[FAIL] {stem}: {e}")
            fail += 1
            continue

        preview = instructions[:80].replace("\n", " ")
        if args.dry_run:
            print(f"[DRY-RUN] {stem} -> agent {agent_id} ({len(instructions)} chars): {preview}...")
            ok += 1
            continue

        try:
            client.update_agent_instructions(args.workspace, agent_id, instructions)
            print(f"[OK] {stem} -> {agent_id} ({len(instructions)} chars)")
            ok += 1
        except MulticaError as e:
            print(f"[FAIL] {stem} -> {agent_id}: {e}")
            fail += 1

    print(f"\nDone: {ok} ok, {fail} failed")
    return 0 if fail == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
