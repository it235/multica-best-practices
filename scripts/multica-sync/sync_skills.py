#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sync templates/<lang>/skills/**/SKILL.md trees to a Multica workspace (default lang: zh_CN).

For each skill directory under templates/zh_CN/skills/ (skips _lib/):
  - POST /api/skills when name not present
  - PUT  /api/skills/{id} when name exists (overwrite content + files)

Payload mirrors the server import layout: full SKILL.md as `content`, other
text files as `files[]` (SKILL.md is never duplicated in files).

Auth (env): same as sync_agents.py

Examples:
  python sync_skills.py --workspace 100
  python sync_skills.py --workspace 100 --dry-run
  python sync_skills.py --workspace 100 --only multica-verification
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from multica_client import MulticaClient, MulticaError, utf8_stdio
from repo_paths import skills_dir

REPO_ROOT = Path(__file__).resolve().parents[2]
SKILLS_ROOT = skills_dir()

FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
NAME_RE = re.compile(r"^name:\s*(.+?)\s*$", re.MULTILINE)
DESC_RE = re.compile(r"^description:\s*(.+?)\s*$", re.MULTILINE)

SKIP_DIR_NAMES = {"_lib", "__pycache__", ".git", "node_modules", ".venv"}
SKIP_FILE_NAMES = {".env", ".env.example"}


def parse_frontmatter(skill_md: str) -> tuple[str, str]:
    name = ""
    description = ""
    m = FRONTMATTER_RE.match(skill_md)
    if m:
        block = m.group(1)
        nm = NAME_RE.search(block)
        dm = DESC_RE.search(block)
        if nm:
            name = nm.group(1).strip().strip("'\"")
        if dm:
            description = dm.group(1).strip().strip("'\"")
    return name, description


def is_ignored_relative(rel: str) -> bool:
    parts = rel.replace("\\", "/").split("/")
    for seg in parts:
        if not seg or seg.startswith(".") or seg in ("__MACOSX", "__pycache__"):
            return True
    if parts[-1].endswith(".pyc"):
        return True
    base = parts[-1].lower()
    if base in SKIP_FILE_NAMES or base.startswith(".env"):
        return True
    if base in ("license", "license.md", "license.txt"):
        return True
    return False


def collect_skill_dirs() -> list[Path]:
    dirs: list[Path] = []
    for skill_md in sorted(SKILLS_ROOT.rglob("SKILL.md")):
        if any(part in SKIP_DIR_NAMES for part in skill_md.parts):
            continue
        dirs.append(skill_md.parent)
    return dirs


def collect_files(skill_dir: Path) -> list[dict[str, str]]:
    files: list[dict[str, str]] = []
    for path in sorted(skill_dir.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(skill_dir).as_posix()
        if rel.lower() == "skill.md" or is_ignored_relative(rel):
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            print(f"  [WARN] skip binary/non-utf8: {rel}")
            continue
        files.append({"path": rel, "content": content})
    return files


def build_payload(skill_dir: Path) -> dict:
    skill_md_path = skill_dir / "SKILL.md"
    content = skill_md_path.read_text(encoding="utf-8")
    name, description = parse_frontmatter(content)
    if not name:
        name = skill_dir.name
    return {
        "name": name,
        "description": description,
        "content": content,
        "config": {},
        "files": collect_files(skill_dir),
    }


def index_skills_by_name(skills: list[dict]) -> dict[str, dict]:
    return {s.get("name", ""): s for s in skills if s.get("name")}


def main() -> int:
    utf8_stdio()
    parser = argparse.ArgumentParser(description="Sync templates/skills to Multica workspace")
    parser.add_argument("--workspace", required=True, help="Workspace slug or UUID")
    parser.add_argument("--url", help="Multica base URL (or MULTICA_API_URL)")
    parser.add_argument("--token", help="API token (or MULTICA_API_TOKEN)")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--only", action="append", help="Sync only these skill names (repeatable)")
    args = parser.parse_args()

    try:
        client = MulticaClient.from_env(args.url, require_auth=not args.dry_run)
        if args.token:
            client.token = args.token
    except MulticaError as e:
        print(str(e), file=sys.stderr)
        return 1

    existing = {}
    if not args.dry_run:
        try:
            existing = index_skills_by_name(client.list_skills(args.workspace))
        except MulticaError as e:
            print(str(e), file=sys.stderr)
            return 1

    only = set(args.only or [])
    created = updated = skipped = failed = 0

    for skill_dir in collect_skill_dirs():
        try:
            payload = build_payload(skill_dir)
        except OSError as e:
            print(f"[FAIL] {skill_dir.name}: {e}")
            failed += 1
            continue

        name = payload["name"]
        if only and name not in only:
            continue

        file_count = len(payload["files"])
        if args.dry_run:
            print(f"[DRY-RUN] sync {name} ({file_count} files, {len(payload['content'])} chars)")
            continue

        try:
            if name in existing:
                skill_id = existing[name]["id"]
                update_body = {
                    "description": payload["description"],
                    "content": payload["content"],
                    "files": payload["files"],
                }
                client.update_skill(args.workspace, skill_id, update_body)
                print(f"[UPDATE] {name} ({skill_id}, {file_count} files)")
                updated += 1
            else:
                client.create_skill(args.workspace, payload)
                print(f"[CREATE] {name} ({file_count} files)")
                created += 1
                existing[name] = {"id": "new", "name": name}
        except MulticaError as e:
            print(f"[FAIL] {name}: {e}")
            failed += 1

    print(f"\nDone: {created} created, {updated} updated, {skipped} skipped, {failed} failed")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
