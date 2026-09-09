#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build template stem -> agent_id mapping from squad members API."""

from __future__ import annotations

import re

from multica_client import MulticaClient, MulticaError

# squad member `role` -> templates/agents/{stem}.md (unique roles)
ROLE_TO_STEM: dict[str, str] = {
    "Leader": "leader",
    "Architect": "architect",
    "BackendDev": "backend-developer",
    "FrontendDev": "frontend-developer",
    "Designer": "designer",
    "ProductManager": "product-manager",
    "Tester": "tester",
    "DevOps": "devops",
}

# Agent name keyword (case-insensitive) -> reviewer template stem
REVIEWER_NAME_HINTS: list[tuple[str, str]] = [
    ("productreviewer", "product-reviewer"),
    ("archreviewer", "arch-reviewer"),
    ("designreviewer", "design-reviewer"),
    ("frontendreviewer", "frontend-reviewer"),
    ("backendreviewer", "backend-reviewer"),
    ("testreviewer", "test-reviewer"),
    ("reviewer", "reviewer"),
]

# Bound skill name -> reviewer template stem (more reliable when present)
REVIEWER_SKILL_TO_STEM: dict[str, str] = {
    "multica-review-product": "product-reviewer",
    "multica-review-architect": "arch-reviewer",
    "multica-review-designer": "design-reviewer",
    "multica-review-frontend": "frontend-reviewer",
    "multica-review-backend": "backend-reviewer",
    "multica-review-test": "test-reviewer",
}


def _normalize_key(text: str) -> str:
    return re.sub(r"[^a-z0-9]", "", text.lower())


def resolve_reviewer_stem(agent_name: str, skill_names: list[str]) -> str | None:
    """Pick reviewer template stem from agent name and/or bound skills."""
    for skill in skill_names:
        if skill in REVIEWER_SKILL_TO_STEM:
            return REVIEWER_SKILL_TO_STEM[skill]

    key = _normalize_key(agent_name)
    for hint, stem in REVIEWER_NAME_HINTS:
        if hint in key:
            return stem
    return None


def build_mapping_from_squad(
    client: MulticaClient,
    workspace: str,
    squad_id: str,
) -> tuple[dict[str, str], list[str]]:
    """
    Fetch squad members and return (stem -> agent_id, warnings).

    Each template stem appears at most once. Duplicate stems log a warning and
    keep the first match.
    """
    members = client.list_squad_members(workspace, squad_id)
    mapping: dict[str, str] = {}
    warnings: list[str] = []

    agent_members = [m for m in members if m.get("member_type") == "agent"]
    if not agent_members:
        raise MulticaError(f"Squad {squad_id} has no agent members")

    for member in agent_members:
        role = member.get("role") or ""
        agent_id = member.get("member_id") or ""
        if not agent_id:
            warnings.append(f"skip member without member_id: {member}")
            continue

        stem: str | None = None
        agent_name = ""

        if role in ROLE_TO_STEM:
            stem = ROLE_TO_STEM[role]
        elif role == "Reviewer":
            try:
                agent = client.get_agent(workspace, agent_id)
                agent_name = agent.get("name") or ""
                skills = client.list_agent_skills(workspace, agent_id)
                skill_names = [s.get("name", "") for s in skills]
                stem = resolve_reviewer_stem(agent_name, skill_names)
                if not stem:
                    warnings.append(
                        f"Reviewer {agent_id} ({agent_name!r}) — cannot match template; "
                        f"skills={skill_names or '(none)'}"
                    )
            except MulticaError as e:
                warnings.append(f"Reviewer {agent_id}: {e}")
                continue
        else:
            warnings.append(f"unknown role {role!r} for agent {agent_id}")
            continue

        if not stem:
            continue
        if stem in mapping:
            warnings.append(
                f"duplicate stem {stem!r}: keep {mapping[stem]}, skip {agent_id} ({agent_name or role})"
            )
            continue
        mapping[stem] = agent_id

    if not mapping:
        raise MulticaError(f"No mappable agents in squad {squad_id}")
    return mapping, warnings
