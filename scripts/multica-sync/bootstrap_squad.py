#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Bootstrap a complete Multica squad from this repo's templates.

Pipeline — each step feeds the next:

  1. skills    templates/zh_CN/skills/**/SKILL.md  -> POST /api/skills | PUT /api/skills/{id}
  2. agents    templates/zh_CN/agents/<stem>.md    -> POST /api/agents | PUT /api/agents/{id}
  3. squad     templates/zh_CN/squad/**/squad.md   -> POST /api/squads (+ PUT instructions)

Template paths are resolved by repo_paths.py (default zh_CN; override with
MULTICA_TEMPLATES_DIR or MULTICA_TEMPLATE_LANG).
  4. members   POST /api/squads/{id}/members   (member_type=agent, role=<role>)
  5. bindings  POST /api/agents/{id}/skills/add  (ensure, additive)
              PUT  /api/agents/{id}/skills       (replace, exact set)

Idempotent by design: re-running updates what already exists and only creates
what is missing. The join key is always the *name* (agent name, skill name,
squad name), so no UUID or internal host ever needs to be committed.

Auth (env):
  MULTICA_API_TOKEN                  Bearer token (recommended)
  MULTICA_COOKIE + MULTICA_CSRF      Browser session fallback
Base URL:
  --url | MULTICA_API_URL | config.local.json  (see multica_client.resolve_base_url)

Examples:
  python bootstrap_squad.py --workspace 100                 # uses squad-bootstrap.json, else the shipped example
  python bootstrap_squad.py --workspace 100 --dry-run
  python bootstrap_squad.py --workspace 100 --config squad-bootstrap.json
  python bootstrap_squad.py --workspace 100 --config squad-bootstrap.json --bind-mode replace
  python bootstrap_squad.py --workspace 100 --config squad-bootstrap.json --write-mapping agent-mapping.json
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from multica_client import MulticaClient, MulticaError, load_local_config, utf8_stdio
from repo_paths import agents_dir, resolve_template_file
from sync_agents import extract_instructions
from sync_skills import build_payload, collect_skill_dirs, index_skills_by_name

REPO_ROOT = Path(__file__).resolve().parents[2]
AGENTS_DIR = agents_dir()
SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_CONFIG = SCRIPT_DIR / "squad-bootstrap.json"
EXAMPLE_CONFIG = SCRIPT_DIR / "squad-bootstrap.example.json"

# A list endpoint may answer with a bare array or an envelope; accept both.
LIST_KEYS = ("squads", "agents", "skills", "runtimes", "members", "items", "data", "results")


def as_list(data) -> list:
    """Normalise a list endpoint response into a list of dicts."""
    if data is None:
        return []
    if isinstance(data, list):
        return [x for x in data if isinstance(x, dict)]
    if isinstance(data, dict):
        for key in LIST_KEYS:
            value = data.get(key)
            if isinstance(value, list):
                return [x for x in value if isinstance(x, dict)]
    return []


def roles_match(existing: str, desired: str) -> bool:
    """Treat role labels case-insensitively (server may use leader vs Leader)."""
    if existing == desired:
        return True
    return existing.lower() == desired.lower()


def load_config(path: Path) -> dict:
    if not path.is_file():
        raise MulticaError(
            f"Config not found: {path}\n"
            f"Copy {EXAMPLE_CONFIG.name} -> {path.name} and adjust names/skills, or pass --config."
        )
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise MulticaError(f"Config must be a JSON object: {path}")
    if not isinstance(data.get("agents"), list) or not data["agents"]:
        raise MulticaError(f"Config needs a non-empty 'agents' list: {path}")
    for spec in data["agents"]:
        if not isinstance(spec, dict) or not spec.get("stem"):
            raise MulticaError(f"Each agent needs a 'stem' (template file name): {path}")
    return data


def resolve_config_path(requested: str | None) -> Path:
    """Pick the config: explicit > squad-bootstrap.json > the shipped example.

    Falling back to the example keeps the happy path to a single command —
    you only create squad-bootstrap.json when you want to customise it.
    """
    if requested:
        path = Path(requested)
        if not path.is_file():
            raise MulticaError(f"Config not found: {path}")
        return path
    if DEFAULT_CONFIG.is_file():
        return DEFAULT_CONFIG
    if EXAMPLE_CONFIG.is_file():
        print(f"[INFO] {DEFAULT_CONFIG.name} not found; using {EXAMPLE_CONFIG.name}")
        return EXAMPLE_CONFIG
    raise MulticaError(f"Neither {DEFAULT_CONFIG.name} nor {EXAMPLE_CONFIG.name} found")


def read_instructions(path: Path) -> str:
    """Prefer the ```text block (Agent Instructions); fall back to raw content."""
    text = path.read_text(encoding="utf-8")
    try:
        return extract_instructions(text)
    except ValueError:
        return text.strip()


def resolve_workspace(cli_value: str) -> str:
    ws = (cli_value or os.environ.get("MULTICA_WORKSPACE") or "").strip()
    if not ws:
        ws = str(load_local_config().get("workspace") or "").strip()
    if not ws:
        raise MulticaError("Missing workspace: pass --workspace or set MULTICA_WORKSPACE")
    return ws


def resolve_runtime(client: MulticaClient, workspace: str, cli_runtime: str) -> str:
    """Agent creation requires runtime_id; pick one when not given explicitly."""
    if cli_runtime:
        return cli_runtime
    runtimes = as_list(client.list_runtimes(workspace))
    if not runtimes:
        raise MulticaError(
            "No agent runtime visible in this workspace. "
            "Pass --runtime <runtime-id> (see: GET /api/runtimes)."
        )
    usable = [r for r in runtimes if r.get("id")]
    if not usable:
        raise MulticaError("Runtimes returned without ids; pass --runtime <runtime-id>")
    for r in usable:
        status = str(r.get("status") or "").lower()
        if status in ("", "online", "connected", "ready"):
            return r["id"]
    return usable[0]["id"]


def load_template_skills() -> dict[str, dict]:
    """skill name -> payload, built from every templates/skills/**/SKILL.md."""
    payloads: dict[str, dict] = {}
    for skill_dir in collect_skill_dirs():
        try:
            payload = build_payload(skill_dir)
        except OSError as e:
            print(f"  [WARN] skip {skill_dir.name}: {e}")
            continue
        payloads[payload["name"]] = payload
    return payloads


def ensure_skills(
    client: MulticaClient,
    workspace: str,
    names: list[str],
    templates: dict[str, dict],
    dry_run: bool,
) -> dict[str, str]:
    """Create/update the requested skills. Returns name -> skill id."""
    remote = index_skills_by_name(as_list(client.list_skills(workspace)))
    resolved: dict[str, str] = {}
    for name in sorted(set(names)):
        payload = templates.get(name)
        if payload is None:
            print(f"[SKIP] skill {name}: no SKILL.md under templates/skills")
            continue
        file_count = len(payload["files"])
        if dry_run:
            action = "update" if name in remote else "create"
            print(f"[DRY-RUN] skill {name}: {action} ({file_count} files)")
            resolved[name] = "dry-run"
            continue
        try:
            if name in remote:
                skill_id = remote[name]["id"]
                client.update_skill(
                    workspace,
                    skill_id,
                    {
                        "description": payload["description"],
                        "content": payload["content"],
                        "files": payload["files"],
                    },
                )
                print(f"[UPDATE] skill {name} ({skill_id}, {file_count} files)")
            else:
                created = client.create_skill(workspace, payload) or {}
                skill_id = created.get("id") or ""
                print(f"[CREATE] skill {name} ({skill_id or '?'} , {file_count} files)")
            if skill_id:
                resolved[name] = skill_id
        except MulticaError as e:
            print(f"[FAIL] skill {name}: {e}")
    return resolved


def ensure_agents(
    client: MulticaClient,
    workspace: str,
    config: dict,
    skill_ids: dict[str, str],
    runtime_id: str,
    dry_run: bool,
    only: set[str] | None,
) -> dict[str, str]:
    """Create/update agents. Returns stem -> agent id."""
    defaults = config.get("defaults") or {}
    specs = [a for a in config["agents"] if not only or a["stem"] in only]
    existing = {a.get("name", ""): a for a in as_list(client.list_agents(workspace))}
    resolved: dict[str, str] = {}

    for spec in specs:
        stem = spec["stem"]
        name = spec.get("name") or stem
        template_path = AGENTS_DIR / f"{stem}.md"
        if not template_path.is_file():
            print(f"[SKIP] agent {stem}: template missing at {template_path}")
            continue

        try:
            instructions = read_instructions(template_path)
        except OSError as e:
            print(f"[FAIL] agent {stem}: {e}")
            continue

        desired = [skill_ids[s] for s in spec.get("skills", []) if s in skill_ids]

        if name in existing:
            agent_id = existing[name]["id"]
            if dry_run:
                print(f"[DRY-RUN] agent {name}: update instructions ({len(instructions)} chars)")
            else:
                try:
                    client.update_agent_instructions(workspace, agent_id, instructions)
                    print(f"[UPDATE] agent {name} ({agent_id})")
                except MulticaError as e:
                    print(f"[FAIL] agent {name}: {e}")
                    continue
        else:
            body = {
                "name": name,
                "description": spec.get("description", defaults.get("description", "")),
                "instructions": instructions,
                "conversation_starters": spec.get("conversation_starters", []),
                "runtime_id": spec.get("runtime_id") or runtime_id,
                "visibility": spec.get("visibility", defaults.get("visibility", "workspace")),
                "skill_ids": desired,
            }
            if dry_run:
                print(
                    f"[DRY-RUN] agent {name}: create "
                    f"(runtime={body['runtime_id'] or 'MISSING'}, {len(desired)} skills)"
                )
                agent_id = "dry-run"
            else:
                if not body["runtime_id"]:
                    print(f"[FAIL] agent {name}: runtime_id required to create (pass --runtime)")
                    continue
                try:
                    created = client.create_agent(workspace, body) or {}
                    agent_id = created.get("id") or ""
                    print(f"[CREATE] agent {name} ({agent_id or '?'})")
                except MulticaError as e:
                    print(f"[FAIL] agent {name}: {e}")
                    continue
        if agent_id:
            resolved[stem] = agent_id
    return resolved


def ensure_squad(
    client: MulticaClient,
    workspace: str,
    config: dict,
    agent_ids: dict[str, str],
    dry_run: bool,
) -> str:
    """Create/update the squad and set its instructions. Returns squad id."""
    squad_cfg = config.get("squad") or {}
    name = squad_cfg.get("name") or "软件开发小队"
    description = squad_cfg.get("description", "")

    instructions = ""
    if squad_cfg.get("instructions_file"):
        path = resolve_template_file(squad_cfg["instructions_file"])
        if path.is_file():
            instructions = read_instructions(path)
        else:
            print(f"[WARN] squad instructions file missing: {path}")

    leader_stem = squad_cfg.get("leader") or "leader"
    leader_id = agent_ids.get(leader_stem, "")

    existing = {s.get("name", ""): s for s in as_list(client.list_squads(workspace))}

    if name in existing:
        squad_id = existing[name]["id"]
        if dry_run:
            print(f"[DRY-RUN] squad {name}: update ({squad_id})")
            return squad_id
        body = {"description": description}
        if instructions:
            body["instructions"] = instructions
        if leader_id:
            body["leader_id"] = leader_id
        try:
            client.update_squad(workspace, squad_id, body)
            print(f"[UPDATE] squad {name} ({squad_id})")
        except MulticaError as e:
            print(f"[FAIL] squad {name}: {e}")
        return squad_id

    if dry_run:
        print(f"[DRY-RUN] squad {name}: create (leader={leader_stem}/{leader_id or 'MISSING'})")
        return "dry-run"

    if not leader_id:
        raise MulticaError(
            f"Cannot create squad: leader agent {leader_stem!r} is unresolved. "
            "Check that its template exists and it was created."
        )
    created = client.create_squad(
        workspace,
        {"name": name, "description": description, "leader_id": leader_id},
    ) or {}
    squad_id = created.get("id") or ""
    if not squad_id:
        raise MulticaError(f"Squad creation returned no id: {created}")
    print(f"[CREATE] squad {name} ({squad_id})")

    if instructions:
        try:
            client.update_squad(workspace, squad_id, {"instructions": instructions})
            print(f"[UPDATE] squad instructions ({len(instructions)} chars)")
        except MulticaError as e:
            print(f"[WARN] squad instructions not applied: {e}")
    return squad_id


def ensure_members(
    client: MulticaClient,
    workspace: str,
    squad_id: str,
    config: dict,
    agent_ids: dict[str, str],
    dry_run: bool,
) -> None:
    """Add every agent to the squad with its declared role."""
    current = {m.get("member_id"): m for m in as_list(client.list_squad_members(workspace, squad_id))}
    for spec in config["agents"]:
        stem = spec["stem"]
        agent_id = agent_ids.get(stem)
        if not agent_id:
            continue
        role = spec.get("role", "")
        if agent_id in current:
            existing_role = current[agent_id].get("role") or ""
            if existing_role == role:
                continue
            if dry_run:
                print(f"[DRY-RUN] member {stem}: role {existing_role!r} -> {role!r}")
            else:
                print(f"[INFO] member {stem} already present with role {existing_role!r}; "
                      f"re-add skipped (change role in the UI or delete the member first)")
            continue
        if dry_run:
            print(f"[DRY-RUN] member {stem}: add as {role or '(no role)'}")
            continue
        try:
            client.add_squad_member(workspace, squad_id, agent_id, role=role)
            print(f"[ADD] member {stem} -> {agent_id} ({role or 'no role'})")
        except MulticaError as e:
            print(f"[FAIL] member {stem}: {e}")


def ensure_bindings(
    client: MulticaClient,
    workspace: str,
    config: dict,
    agent_ids: dict[str, str],
    skill_ids: dict[str, str],
    mode: str,
    dry_run: bool,
) -> None:
    """Bind the declared skills to each agent. `ensure` adds, `replace` sets exact."""
    for spec in config["agents"]:
        stem = spec["stem"]
        agent_id = agent_ids.get(stem)
        if not agent_id:
            continue
        desired = [skill_ids[s] for s in spec.get("skills", []) if s in skill_ids]
        if not desired:
            continue

        if dry_run:
            print(f"[DRY-RUN] bind {stem}: {len(desired)} skills ({mode})")
            continue

        try:
            current = as_list(client.list_agent_skills(workspace, agent_id))
        except MulticaError as e:
            print(f"[FAIL] bind {stem}: cannot read current skills: {e}")
            continue
        current_ids = {s.get("id") for s in current if s.get("id")}

        if mode == "replace":
            if current_ids == set(desired):
                print(f"[OK] bind {stem}: already {len(desired)} skills")
                continue
            try:
                client.set_agent_skills(workspace, agent_id, desired)
                print(f"[SET] bind {stem}: {len(desired)} skills (replace)")
            except MulticaError as e:
                print(f"[FAIL] bind {stem}: {e}")
            continue

        missing = [sid for sid in desired if sid not in current_ids]
        if not missing:
            print(f"[OK] bind {stem}: already {len(desired)} skills")
            continue
        try:
            client.add_agent_skills(workspace, agent_id, missing)
            print(f"[BIND] {stem}: +{len(missing)} skills")
        except MulticaError as e:
            print(f"[FAIL] bind {stem}: {e}")


def main() -> int:
    utf8_stdio()
    parser = argparse.ArgumentParser(
        description="Bootstrap a full Multica squad (skills + agents + squad + members + bindings)"
    )
    parser.add_argument("--workspace", help="Workspace slug or UUID (or MULTICA_WORKSPACE)")
    parser.add_argument(
        "--config",
        help=f"Bootstrap config JSON (default: {DEFAULT_CONFIG.name}; falls back to {EXAMPLE_CONFIG.name})",
    )
    parser.add_argument("--url", help="Multica base URL (or MULTICA_API_URL)")
    parser.add_argument("--token", help="API token (or MULTICA_API_TOKEN)")
    parser.add_argument("--runtime", help="Agent runtime_id for created agents (auto-detected)")
    parser.add_argument(
        "--sync-skills",
        choices=("needed", "all", "none"),
        default="needed",
        help="needed = skills referenced by config (default); all = every template skill; none = skip",
    )
    parser.add_argument(
        "--bind-mode",
        choices=("ensure", "replace"),
        default="ensure",
        help="ensure = add missing bindings (default); replace = set the exact list",
    )
    parser.add_argument("--dry-run", action="store_true", help="Print actions without writing")
    parser.add_argument("--only", action="append", help="Only these agent stems (repeatable)")
    parser.add_argument("--write-mapping", help="Write stem -> agent_id JSON for sync_agents.py --mapping")
    args = parser.parse_args()

    try:
        config = load_config(resolve_config_path(args.config))
        workspace = resolve_workspace(args.workspace)
        client = MulticaClient.from_env(args.url)
        if args.token:
            client.token = args.token
    except (MulticaError, OSError, ValueError) as e:
        print(str(e), file=sys.stderr)
        return 1

    only = set(args.only or [])
    if only:
        unknown = only - {a["stem"] for a in config["agents"]}
        if unknown:
            print(f"Unknown --only stems (not in config): {', '.join(sorted(unknown))}", file=sys.stderr)
            return 1

    print(f"Workspace: {workspace}  (dry-run: {args.dry_run})")

    templates = load_template_skills()
    print(f"Found {len(templates)} skills in templates/skills")

    # 1. Skills
    if args.sync_skills == "none":
        skill_ids: dict[str, str] = {}
    else:
        wanted: list[str] = []
        for spec in config["agents"]:
            if only and spec["stem"] not in only:
                continue
            wanted.extend(spec.get("skills", []))
        if args.sync_skills == "all":
            wanted = list(templates)
        skill_ids = ensure_skills(client, workspace, wanted, templates, args.dry_run)

    # Re-index by name so bindings resolve even when skills were skipped:
    # fall back to whatever already exists remotely.
    if args.sync_skills == "none" or args.dry_run:
        try:
            remote = index_skills_by_name(as_list(client.list_skills(workspace)))
        except MulticaError as e:
            print(f"[WARN] cannot list remote skills: {e}")
            remote = {}
        for name, skill in remote.items():
            skill_ids.setdefault(name, skill["id"])

    # 2. Runtime (only needed when creating agents)
    runtime_id = ""
    try:
        runtime_id = resolve_runtime(client, workspace, args.runtime)
    except MulticaError as e:
        # Not fatal: existing agents can still be updated without a runtime.
        print(f"[WARN] {e}")

    # 3. Agents
    agent_ids = ensure_agents(client, workspace, config, skill_ids, runtime_id, args.dry_run, only)

    # 4. Squad
    try:
        squad_id = ensure_squad(client, workspace, config, agent_ids, args.dry_run)
    except MulticaError as e:
        print(str(e), file=sys.stderr)
        return 1

    # 5. Members + bindings
    if squad_id and squad_id != "dry-run":
        ensure_members(client, workspace, squad_id, config, agent_ids, args.dry_run)
    ensure_bindings(client, workspace, config, agent_ids, skill_ids, args.bind_mode, args.dry_run)

    if args.write_mapping and not args.dry_run:
        try:
            Path(args.write_mapping).write_text(
                json.dumps(dict(sorted(agent_ids.items())), ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            print(f"\nMapping written: {args.write_mapping}")
        except OSError as e:
            print(f"[WARN] cannot write mapping: {e}")

    print(f"\nDone: {len(skill_ids)} skills, {len(agent_ids)} agents, squad={squad_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
