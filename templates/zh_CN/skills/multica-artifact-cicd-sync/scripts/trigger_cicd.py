#!/usr/bin/env python3
"""CI/CD orchestrator — cross-platform (Windows / Linux)."""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import yaml

SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
sys.path.insert(0, str(SCRIPT_DIR))

from 按 skill 名 import resolve_skill_dir  # noqa: E402


def run_python(script: Path, args: list[str]) -> tuple[int, str]:
    proc = subprocess.run(
        [sys.executable, str(script), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    output = (proc.stdout or "") + (proc.stderr or "")
    if proc.stdout:
        print(proc.stdout, end="")
    if proc.stderr:
        print(proc.stderr, end="", file=sys.stderr)
    return proc.returncode, output


def append_jira(issue: str, wiki: str, jira_skill: Path) -> None:
    jira_sh = jira_skill / "scripts" / "jira.sh"
    if not jira_sh.is_file():
        print("WARN: jira.sh not found, skip JIRA append", file=sys.stderr)
        return
    bash = shutil.which("bash")
    if not bash:
        print("WARN: bash not found, skip JIRA append (install Git Bash on Windows)", file=sys.stderr)
        return
    subprocess.run([bash, str(jira_sh), "append-description", issue, wiki], check=False)


def resolve_services_from_issue(orch_cfg: dict, issue: str, env: str) -> list[str]:
    if not issue:
        return []
    prefix = issue.split("-")[0]
    mapping = (orch_cfg.get("issue_service_map") or {}).get(prefix, {})
    if isinstance(mapping, dict):
        services = mapping.get(env) or mapping.get("sit") or mapping.get("dev") or []
        return list(services)
    return []


def main() -> int:
    parser = argparse.ArgumentParser(description="multica-artifact-cicd-sync")
    parser.add_argument("--issue", default="")
    parser.add_argument("--branch", default="")
    parser.add_argument("--param", action="append", default=[], help="Override Jenkins param key=value")
    parser.add_argument("--discover-only", action="store_true")
    parser.add_argument("--no-last-success", action="store_true", help="Do not seed params from last SUCCESS build")
    parser.add_argument("--env", default="", choices=("", "dev", "sit"), help="dev or sit (default from config)")
    parser.add_argument("--service", action="append", default=[], help="Logical service e.g. acme")
    parser.add_argument("--profile", default="", help="Deprecated alias for --env sit|dev")
    parser.add_argument("--promote-prod", action="store_true", help="Legacy projectmanagement flow only")
    parser.add_argument("--project", action="append", default=[])
    parser.add_argument("--version", action="append", default=[])
    parser.add_argument("--job-path", default="")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    config_path = SKILL_DIR / "config.yaml"
    orch_cfg = yaml.safe_load(config_path.read_text(encoding="utf-8")) if config_path.is_file() else {}

    env = args.env or args.profile or (orch_cfg.get("defaults") or {}).get("environment", "sit")
    if env == "prod":
        env = "sit"  # no prod catalog yet; use legacy promote_prod path below

    jenkins_skill = resolve_skill_dir("multica-platform-jenkins", SKILL_DIR)
    jenkins_scripts = jenkins_skill / "scripts"
    jenkins_cfg = yaml.safe_load((jenkins_skill / "config.yaml").read_text(encoding="utf-8"))

    services = list(args.service)
    if not services and args.issue:
        services = resolve_services_from_issue(orch_cfg, args.issue, env)
    if not services and os.environ.get("BUILD_SERVICES"):
        services = [s.strip() for s in os.environ["BUILD_SERVICES"].split(",") if s.strip()]

    rc = 0
    log = ""

    if args.job_path:
        tw_args = ["trigger-wait", "--job-path", args.job_path]
        if args.branch:
            tw_args.extend(["--branch", args.branch])
        for p in args.param:
            tw_args.extend(["--param", p])
        if args.no_last_success:
            tw_args.append("--no-last-success")
        rc, log = run_python(jenkins_scripts / "jenkins_cli.py", tw_args)
    elif args.promote_prod or (args.profile == "prod"):
        if args.project:
            if len(args.project) != len(args.version):
                print("ERROR: each --project needs --version", file=sys.stderr)
                return 1
            pp_args: list[str] = []
            for p, v in zip(args.project, args.version, strict=True):
                pp_args.extend(["--project", p, "--version", v])
            rc, log = run_python(jenkins_scripts / "promote_prod.py", pp_args)
        else:
            rc, log = run_python(jenkins_scripts / "promote_prod.py", [])
    elif services:
        te_args = ["--env", env]
        for svc in services:
            te_args.extend(["--service", svc])
        if args.branch:
            te_args.extend(["--branch", args.branch])
        if args.issue:
            te_args.extend(["--issue", args.issue])
        if args.discover_only:
            te_args.append("--discover-only")
        if args.no_last_success:
            te_args.append("--no-last-success")
        for p in args.param:
            te_args.extend(["--param", p])
        if args.json:
            te_args.append("--json")
        rc, log = run_python(jenkins_scripts / "trigger_env.py", te_args)
    else:
        print("ERROR: specify --service acme or configure issue_service_map for Issue prefix", file=sys.stderr)
        return 1

    build_urls = sorted(set(re.findall(r"https?://[^\s]+/job/[^\s/]+(?:/[^/\s]+)?/\d+/?", log)))

    deploy_base = ((jenkins_cfg.get("environments") or {}).get(env) or {}).get("deploy_base_url", "")

    append = (orch_cfg.get("defaults") or {}).get("append_jira", True)
    if append and args.issue and build_urls:
        try:
            jira_skill = resolve_skill_dir("multica-platform-jira", SKILL_DIR)
            heading = (orch_cfg.get("jira") or {}).get("cicd_heading", "h3. CI/CD 部署 (Build / Deploy)")
            wiki = heading + "\n"
            for u in build_urls:
                wiki += f"* [Build|{u}]\n"
            if deploy_base:
                wiki += f"* Deploy base: {deploy_base}\n"
            append_jira(args.issue, wiki, jira_skill)
        except FileNotFoundError as e:
            print(f"WARN: {e}", file=sys.stderr)

    payload = {
        "issue": args.issue,
        "env": env,
        "services": services,
        "branch": args.branch,
        "build_urls": build_urls,
        "deploy_base_url": deploy_base,
    }
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"env: {env}")
        print(f"deploy_base_url: {deploy_base}")
        for u in build_urls:
            print(f"build_url: {u}")

    return rc


if __name__ == "__main__":
    raise SystemExit(main())
