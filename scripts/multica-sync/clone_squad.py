#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Clone a squad from one workspace to another (cross-workspace copy).

Reads the source squad's agents, skills, bindings, and squad metadata from the
API. On the target workspace (all idempotent by *name*):

  1. skills  — create if missing; reuse existing skill id if name already exists
  2. agents  — create if missing (needs runtime on target); reuse if name exists
  3. squad   — create if missing (same name as source); reuse if name exists
  4. members — add missing agent members (+ fix role when different)
  5. bindings — POST /api/agents/{id}/skills/add for skills not yet bound

Existing skills/agents are NOT overwritten unless --update-skills / --update-agents.

Examples:
  python clone_squad.py --from-workspace 100 --from-squad <uuid> --to-workspace 200
  python clone_squad.py --from-workspace 100 --from-squad <uuid> --to-workspace 200 --dry-run
  python clone_squad.py ... --to-workspace 200 --runtime <runtime-id>
  python clone_squad.py ... --update-skills --update-agents --update-squad
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass, field

from bootstrap_squad import as_list, resolve_runtime, roles_match
from multica_client import MulticaClient, MulticaError, utf8_stdio
from sync_skills import index_skills_by_name


@dataclass
class SourceAgent:
    name: str
    role: str
    description: str
    instructions: str
    conversation_starters: list
    skill_names: list[str] = field(default_factory=list)


@dataclass
class SourceSquad:
    name: str
    description: str
    instructions: str
    leader_name: str
    agents: list[SourceAgent]


def skill_to_create_payload(skill: dict) -> dict:
    files = [
        {"path": f["path"], "content": f.get("content", "")}
        for f in skill.get("files") or []
        if f.get("path")
    ]
    return {
        "name": skill.get("name") or "",
        "description": skill.get("description") or "",
        "content": skill.get("content") or "",
        "config": skill.get("config") or {},
        "files": files,
    }


def fetch_source_squad(
    client: MulticaClient,
    workspace: str,
    squad_id: str,
) -> SourceSquad:
    squad = client.get_squad(workspace, squad_id)
    if not squad:
        raise MulticaError(f"Source squad not found: {squad_id}")

    leader_id = squad.get("leader_id") or ""
    members = [
        m for m in as_list(client.list_squad_members(workspace, squad_id))
        if m.get("member_type") == "agent"
    ]
    if not members:
        raise MulticaError(f"Source squad {squad_id} has no agent members")

    agents: list[SourceAgent] = []
    leader_name = ""

    for member in members:
        agent_id = member.get("member_id") or ""
        if not agent_id:
            continue
        detail = client.get_agent(workspace, agent_id)
        name = detail.get("name") or agent_id
        if agent_id == leader_id:
            leader_name = name
        bound = as_list(client.list_agent_skills(workspace, agent_id))
        skill_names = [s.get("name", "") for s in bound if s.get("name")]
        agents.append(
            SourceAgent(
                name=name,
                role=member.get("role") or "",
                description=detail.get("description") or "",
                instructions=detail.get("instructions") or "",
                conversation_starters=detail.get("conversation_starters") or [],
                skill_names=skill_names,
            )
        )

    if not leader_name:
        for a in agents:
            if a.role.lower() == "leader":
                leader_name = a.name
                break
        if not leader_name and agents:
            leader_name = agents[0].name

    return SourceSquad(
        name=squad.get("name") or "squad",
        description=squad.get("description") or "",
        instructions=squad.get("instructions") or "",
        leader_name=leader_name,
        agents=agents,
    )


def collect_source_skills(
    client: MulticaClient,
    workspace: str,
    source: SourceSquad,
) -> dict[str, dict]:
    """skill name -> full skill payload (content + files) from source workspace."""
    listed = index_skills_by_name(as_list(client.list_skills(workspace)))
    needed_names: set[str] = set()
    for agent in source.agents:
        needed_names.update(agent.skill_names)

    payloads: dict[str, dict] = {}
    for name in sorted(needed_names):
        summary = listed.get(name)
        if not summary or not summary.get("id"):
            print(f"[WARN] source skill {name!r} not found in workspace catalog")
            continue
        full = client.get_skill(workspace, summary["id"]) or {}
        if not full.get("name"):
            full["name"] = name
        payloads[name] = full
    return payloads


def ensure_target_skills(
    client: MulticaClient,
    workspace: str,
    source_skills: dict[str, dict],
    dry_run: bool,
    update: bool,
) -> dict[str, str]:
    """Returns skill name -> target skill id."""
    remote = index_skills_by_name(as_list(client.list_skills(workspace)))
    resolved: dict[str, str] = {}

    for name, skill in source_skills.items():
        payload = skill_to_create_payload(skill)
        if name in remote:
            skill_id = remote[name]["id"]
            if dry_run:
                action = "update" if update else "reuse"
                print(f"[DRY-RUN] skill {name}: {action} ({skill_id})")
            elif update:
                client.update_skill(
                    workspace,
                    skill_id,
                    {
                        "description": payload["description"],
                        "content": payload["content"],
                        "files": payload["files"],
                    },
                )
                print(f"[UPDATE] skill {name} ({skill_id})")
            else:
                print(f"[OK] skill {name}: exists ({skill_id})")
            resolved[name] = skill_id
            continue

        if dry_run:
            print(f"[DRY-RUN] skill {name}: create")
            resolved[name] = "dry-run"
            continue
        try:
            created = client.create_skill(workspace, payload) or {}
            skill_id = created.get("id") or ""
            print(f"[CREATE] skill {name} ({skill_id or '?'})")
            if skill_id:
                resolved[name] = skill_id
        except MulticaError as e:
            print(f"[FAIL] skill {name}: {e}")
    return resolved


def ensure_target_agents(
    client: MulticaClient,
    workspace: str,
    source: SourceSquad,
    skill_ids: dict[str, str],
    runtime_id: str,
    dry_run: bool,
    update: bool,
) -> dict[str, str]:
    """Returns agent name -> target agent id."""
    remote = {a.get("name", ""): a for a in as_list(client.list_agents(workspace))}
    resolved: dict[str, str] = {}

    for agent in source.agents:
        desired_skill_ids = [skill_ids[n] for n in agent.skill_names if n in skill_ids]

        if agent.name in remote:
            agent_id = remote[agent.name]["id"]
            if dry_run:
                action = "update instructions" if update else "reuse"
                print(f"[DRY-RUN] agent {agent.name}: {action} ({agent_id})")
            elif update and agent.instructions:
                client.update_agent_instructions(
                    workspace, agent_id, agent.instructions, agent.conversation_starters
                )
                print(f"[UPDATE] agent {agent.name} instructions ({agent_id})")
            else:
                print(f"[OK] agent {agent.name}: exists ({agent_id})")
            resolved[agent.name] = agent_id
            continue

        body = {
            "name": agent.name,
            "description": agent.description,
            "instructions": agent.instructions,
            "conversation_starters": agent.conversation_starters,
            "runtime_id": runtime_id,
            "visibility": "workspace",
            "skill_ids": desired_skill_ids,
        }
        if dry_run:
            print(
                f"[DRY-RUN] agent {agent.name}: create "
                f"(runtime={runtime_id or 'MISSING'}, {len(desired_skill_ids)} skills)"
            )
            resolved[agent.name] = "dry-run"
            continue
        if not runtime_id:
            print(f"[FAIL] agent {agent.name}: runtime_id required (pass --runtime)")
            continue
        try:
            created = client.create_agent(workspace, body) or {}
            agent_id = created.get("id") or ""
            print(f"[CREATE] agent {agent.name} ({agent_id or '?'})")
            if agent_id:
                resolved[agent.name] = agent_id
        except MulticaError as e:
            print(f"[FAIL] agent {agent.name}: {e}")
    return resolved


def ensure_target_squad(
    client: MulticaClient,
    workspace: str,
    source: SourceSquad,
    agent_ids: dict[str, str],
    dry_run: bool,
    update: bool,
    squad_name: str | None,
) -> str:
    name = squad_name or source.name
    leader_id = agent_ids.get(source.leader_name, "")
    existing = {s.get("name", ""): s for s in as_list(client.list_squads(workspace))}

    if name in existing:
        squad_id = existing[name]["id"]
        if dry_run:
            print(f"[DRY-RUN] squad {name}: reuse ({squad_id})")
            return squad_id
        if update:
            body = {
                "description": source.description,
                "instructions": source.instructions,
            }
            if leader_id:
                body["leader_id"] = leader_id
            try:
                client.update_squad(workspace, squad_id, body)
                print(f"[UPDATE] squad {name} ({squad_id})")
            except MulticaError as e:
                print(f"[FAIL] squad {name}: {e}")
        else:
            print(f"[OK] squad {name}: exists ({squad_id})")
        return squad_id

    if dry_run:
        print(f"[DRY-RUN] squad {name}: create (leader={source.leader_name})")
        return "dry-run"

    if not leader_id:
        raise MulticaError(
            f"Cannot create squad {name!r}: leader {source.leader_name!r} not resolved on target"
        )
    created = client.create_squad(
        workspace,
        {"name": name, "description": source.description, "leader_id": leader_id},
    ) or {}
    squad_id = created.get("id") or ""
    if not squad_id:
        raise MulticaError(f"Squad creation returned no id: {created}")
    print(f"[CREATE] squad {name} ({squad_id})")
    if source.instructions:
        try:
            client.update_squad(workspace, squad_id, {"instructions": source.instructions})
            print(f"[UPDATE] squad instructions ({len(source.instructions)} chars)")
        except MulticaError as e:
            print(f"[WARN] squad instructions: {e}")
    return squad_id


def ensure_target_members(
    client: MulticaClient,
    workspace: str,
    squad_id: str,
    source: SourceSquad,
    agent_ids: dict[str, str],
    dry_run: bool,
) -> None:
    if squad_id == "dry-run":
        for agent in source.agents:
            if agent.name in agent_ids:
                print(f"[DRY-RUN] member {agent.name}: add as {agent.role or '(no role)'}")
        return

    current = {m.get("member_id"): m for m in as_list(client.list_squad_members(workspace, squad_id))}
    for agent in source.agents:
        agent_id = agent_ids.get(agent.name)
        if not agent_id or agent_id == "dry-run":
            continue
        role = agent.role
        if agent_id in current:
            existing_role = current[agent_id].get("role") or ""
            if roles_match(existing_role, role):
                continue
            if dry_run:
                print(f"[DRY-RUN] member {agent.name}: role {existing_role!r} -> {role!r}")
                continue
            try:
                client.update_squad_member_role(workspace, squad_id, agent_id, role)
                print(f"[ROLE] member {agent.name}: {existing_role!r} -> {role!r}")
            except MulticaError as e:
                print(f"[FAIL] member {agent.name} role: {e}")
            continue
        if dry_run:
            print(f"[DRY-RUN] member {agent.name}: add as {role or '(no role)'}")
            continue
        try:
            client.add_squad_member(workspace, squad_id, agent_id, role=role)
            print(f"[ADD] member {agent.name} -> {agent_id} ({role or 'no role'})")
        except MulticaError as e:
            print(f"[FAIL] member {agent.name}: {e}")


def ensure_target_bindings(
    client: MulticaClient,
    workspace: str,
    source: SourceSquad,
    agent_ids: dict[str, str],
    skill_ids: dict[str, str],
    dry_run: bool,
) -> None:
    for agent in source.agents:
        agent_id = agent_ids.get(agent.name)
        if not agent_id or agent_id == "dry-run":
            continue
        desired = [skill_ids[n] for n in agent.skill_names if n in skill_ids and skill_ids[n] != "dry-run"]
        if not desired:
            continue
        if dry_run:
            print(f"[DRY-RUN] bind {agent.name}: +{len(desired)} skills (ensure)")
            continue
        try:
            current = as_list(client.list_agent_skills(workspace, agent_id))
        except MulticaError as e:
            print(f"[FAIL] bind {agent.name}: {e}")
            continue
        current_ids = {s.get("id") for s in current if s.get("id")}
        missing = [sid for sid in desired if sid not in current_ids]
        if not missing:
            print(f"[OK] bind {agent.name}: already {len(desired)} skills")
            continue
        try:
            client.add_agent_skills(workspace, agent_id, missing)
            print(f"[BIND] {agent.name}: +{len(missing)} skills")
        except MulticaError as e:
            print(f"[FAIL] bind {agent.name}: {e}")


def main() -> int:
    utf8_stdio()
    parser = argparse.ArgumentParser(
        description="Clone a squad from one workspace to another (create-if-missing + bind)"
    )
    parser.add_argument("--from-workspace", required=True, help="Source workspace slug/UUID")
    parser.add_argument("--from-squad", required=True, help="Source squad UUID")
    parser.add_argument("--to-workspace", required=True, help="Target workspace slug/UUID")
    parser.add_argument("--to-squad-name", help="Target squad name (default: same as source)")
    parser.add_argument("--url", help="Multica base URL")
    parser.add_argument("--token", help="API token")
    parser.add_argument("--runtime", help="Runtime for newly created agents on target")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--update-skills",
        action="store_true",
        help="Overwrite skill content on target when name already exists",
    )
    parser.add_argument(
        "--update-agents",
        action="store_true",
        help="Overwrite agent instructions on target when name already exists",
    )
    parser.add_argument(
        "--update-squad",
        action="store_true",
        help="Overwrite squad metadata on target when name already exists",
    )
    args = parser.parse_args()

    try:
        client = MulticaClient.from_env(args.url)
        if args.token:
            client.token = args.token
    except MulticaError as e:
        print(str(e), file=sys.stderr)
        return 1

    print(f"Clone: workspace {args.from_workspace} squad {args.from_squad}")
    print(f"    -> workspace {args.to_workspace}  (dry-run: {args.dry_run})")

    try:
        source = fetch_source_squad(client, args.from_workspace, args.from_squad)
        print(f"Source: {source.name!r} — {len(source.agents)} agents, leader={source.leader_name!r}")
        source_skills = collect_source_skills(client, args.from_workspace, source)
        print(f"Source skills to copy: {len(source_skills)}")
    except MulticaError as e:
        print(str(e), file=sys.stderr)
        return 1

    skill_ids = ensure_target_skills(
        client, args.to_workspace, source_skills, args.dry_run, args.update_skills
    )

    runtime_id = ""
    if not args.dry_run:
        try:
            runtime_id = resolve_runtime(client, args.to_workspace, args.runtime or "")
        except MulticaError as e:
            print(f"[WARN] {e}")
    elif args.runtime:
        runtime_id = args.runtime

    agent_ids = ensure_target_agents(
        client,
        args.to_workspace,
        source,
        skill_ids,
        runtime_id,
        args.dry_run,
        args.update_agents,
    )

    try:
        squad_id = ensure_target_squad(
            client,
            args.to_workspace,
            source,
            agent_ids,
            args.dry_run,
            args.update_squad,
            args.to_squad_name,
        )
    except MulticaError as e:
        print(str(e), file=sys.stderr)
        return 1

    ensure_target_members(client, args.to_workspace, squad_id, source, agent_ids, args.dry_run)
    ensure_target_bindings(client, args.to_workspace, source, agent_ids, skill_ids, args.dry_run)

    print(
        f"\nDone: {len(skill_ids)} skills, {len(agent_ids)} agents, target squad={squad_id}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
