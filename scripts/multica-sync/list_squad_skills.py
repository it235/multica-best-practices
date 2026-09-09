#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
List all agents in a squad and their bound skills.

Flow:
  1. GET /api/squads/{id}
  2. GET /api/squads/{id}/members
  3. For each member_type == "agent": GET /api/agents/{id}/skills

Auth (env): same as sync_agents.py

Examples:
  python list_squad_skills.py --workspace 100 --squad <squad-uuid>
  python list_squad_skills.py --workspace 100 --squad <squad-uuid> --json
"""

from __future__ import annotations

import argparse
import json
import sys

from multica_client import MulticaClient, MulticaError, utf8_stdio


def main() -> int:
    utf8_stdio()
    parser = argparse.ArgumentParser(description="List squad agents and their skills")
    parser.add_argument("--workspace", required=True, help="Workspace slug or UUID")
    parser.add_argument("--squad", required=True, help="Squad UUID")
    parser.add_argument("--url", help="Multica base URL (or MULTICA_API_URL)")
    parser.add_argument("--token", help="API token (or MULTICA_API_TOKEN)")
    parser.add_argument("--json", dest="as_json", action="store_true", help="JSON output")
    args = parser.parse_args()

    try:
        client = MulticaClient.from_env(args.url)
        if args.token:
            client.token = args.token
    except MulticaError as e:
        print(str(e), file=sys.stderr)
        return 1

    try:
        squad = client.get_squad(args.workspace, args.squad)
        members = client.list_squad_members(args.workspace, args.squad)
    except MulticaError as e:
        print(str(e), file=sys.stderr)
        return 1

    agent_members = [m for m in members if m.get("member_type") == "agent"]
    report = {
        "squad": {
            "id": squad.get("id"),
            "name": squad.get("name"),
            "leader_id": squad.get("leader_id"),
            "member_count": squad.get("member_count"),
        },
        "agents": [],
    }

    for member in agent_members:
        agent_id = member["member_id"]
        role = member.get("role", "")
        try:
            agent = client.get_agent(args.workspace, agent_id)
            skills = client.list_agent_skills(args.workspace, agent_id)
        except MulticaError as e:
            report["agents"].append(
                {
                    "agent_id": agent_id,
                    "role": role,
                    "error": str(e),
                    "skills": [],
                }
            )
            continue

        report["agents"].append(
            {
                "agent_id": agent_id,
                "name": agent.get("name"),
                "role": role,
                "is_leader": agent_id == squad.get("leader_id"),
                "skills": [
                    {
                        "id": s.get("id"),
                        "name": s.get("name"),
                        "description": s.get("description"),
                        "enabled": s.get("enabled"),
                    }
                    for s in skills
                ],
            }
        )

    if args.as_json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0

    print(f"Squad: {report['squad']['name']} ({report['squad']['id']})")
    print(f"Leader agent: {report['squad']['leader_id']}")
    print(f"Agent members: {len(report['agents'])}\n")

    for entry in report["agents"]:
        leader_tag = " [LEADER]" if entry.get("is_leader") else ""
        if entry.get("error"):
            print(f"- {entry.get('name') or entry['agent_id']}{leader_tag} ({entry['role']}) — ERROR: {entry['error']}")
            continue
        skill_names = [s["name"] for s in entry.get("skills", [])]
        enabled = [s["name"] for s in entry.get("skills", []) if s.get("enabled")]
        print(f"- {entry['name']} ({entry['agent_id']}){leader_tag} role={entry['role']}")
        print(f"    skills ({len(skill_names)}): {', '.join(skill_names) or '(none)'}")
        if enabled != skill_names:
            print(f"    enabled: {', '.join(enabled) or '(none)'}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
