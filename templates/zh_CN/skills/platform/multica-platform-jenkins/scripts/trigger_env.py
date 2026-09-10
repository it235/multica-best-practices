#!/usr/bin/env python3
"""Trigger dev / sit Jenkins jobs by service name (cross-platform)."""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from lib.config import load_config  # noqa: E402
from lib.jenkins_client import JenkinsError, parse_deploy_version  # noqa: E402
from lib.jobs_catalog import job_api_path, load_jobs_catalog, resolve_job_name  # noqa: E402
from lib.param_discovery import ParameterDiscovery, resolve_trigger_params  # noqa: E402
from lib import make_client  # noqa: E402


def parse_services(raw: list[str]) -> list[str]:
    out: list[str] = []
    for item in raw:
        out.extend(s.strip() for s in item.split(",") if s.strip())
    env_val = os.environ.get("BUILD_SERVICES", "")
    if env_val:
        out.extend(s.strip() for s in env_val.split(",") if s.strip())
    return out


def overrides_from_cli(extra: list[str]) -> dict[str, str]:
    out: dict[str, str] = {}
    for pair in extra:
        if "=" in pair:
            k, v = pair.split("=", 1)
            out[k] = v
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description="Trigger <jenkins-job-dev> / <jenkins-job-sit> Jenkins jobs")
    parser.add_argument("--env", choices=("dev", "sit"), default="sit")
    parser.add_argument("--service", action="append", default=[], help="Logical service e.g. <service>")
    parser.add_argument("--branch", default="")
    parser.add_argument("--issue", default="")
    parser.add_argument("--param", action="append", default=[], help="Override key=value (wins over auto)")
    parser.add_argument("--discover-only", action="store_true", help="Only fetch params, do not trigger")
    parser.add_argument("--auto-params", action="store_true", default=True)
    parser.add_argument("--no-auto-params", action="store_false", dest="auto_params")
    parser.add_argument("--no-last-success", action="store_true", help="Do not seed params from last SUCCESS build")
    parser.add_argument("--timeout-seconds", type=int)
    parser.add_argument("--poll-interval-seconds", type=int)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    skill_dir = SCRIPT_DIR.parent
    cfg = load_config(skill_dir)
    catalog = load_jobs_catalog(skill_dir)

    services = parse_services(args.service)
    if not services:
        print("ERROR: specify --service <service> or set BUILD_SERVICES", file=sys.stderr)
        return 1

    env_cfg = (cfg.get("environments") or {}).get(args.env, {})
    branch = args.branch or env_cfg.get("default_branch") or cfg.get("defaults", {}).get("branch", "master")
    overrides = overrides_from_cli(args.param)
    use_last_success = not args.no_last_success

    client = make_client(skill_dir)
    if args.timeout_seconds:
        client.timeout = args.timeout_seconds
    if args.poll_interval_seconds:
        client.poll_interval = args.poll_interval_seconds

    discoveries: list[dict] = []
    results: list[dict] = []

    for service in services:
        job_name = resolve_job_name(catalog, args.env, service)
        job_path = job_api_path(job_name)

        if args.auto_params:
            discovery = ParameterDiscovery(client).discover(
                job_path,
                branch=branch,
                env=args.env,
                service=service,
                issue_key=args.issue,
                overrides=overrides,
                use_last_success=use_last_success,
            )
            discoveries.append({"service": service, "job": job_name, **discovery})

            if args.discover_only:
                continue

            if discovery["parameterized"] and not discovery["ready"]:
                missing = ", ".join(discovery["missing"])
                print(
                    f"ERROR: {job_name} missing params: {missing}. "
                    f"Run with --discover-only --json or add --param",
                    file=sys.stderr,
                )
                if args.json:
                    print(json.dumps({"discoveries": discoveries}, ensure_ascii=False, indent=2))
                return 2

            params = discovery["resolved"] if discovery["parameterized"] else {}
        else:
            params = dict((cfg.get("environments") or {}).get(args.env, {}).get("default_params") or {})
            if branch:
                params.setdefault("branchName", branch)
            params.update(overrides)
            if args.discover_only:
                discoveries.append({"service": service, "job": job_name, "resolved": params})
                continue

        print(f"=== Trigger {args.env}/{service} → {job_name} ===")
        print(f"    params: {params}")
        data = client.trigger_and_wait(job_path, params)
        display = data.get("fullDisplayName", "")
        results.append(
            {
                "env": args.env,
                "service": service,
                "job": job_name,
                "params": params,
                "url": data.get("url", ""),
                "number": data.get("number"),
                "result": data.get("result"),
                "displayName": display,
                "deployVersion": parse_deploy_version(display),
            }
        )
        print(f"SUCCESS: {results[-1]['url']}")

    if args.discover_only:
        payload = {"branch": branch, "env": args.env, "discoveries": discoveries}
        print(json.dumps(payload, ensure_ascii=False, indent=2) if args.json else payload)
        return 0 if all(d.get("ready", True) for d in discoveries) else 2

    if args.json:
        print(json.dumps({"branch": branch, "builds": results, "discoveries": discoveries}, ensure_ascii=False, indent=2))
    else:
        print("--- summary ---")
        for r in results:
            print(r["url"])

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (JenkinsError, KeyError) as e:
        print(f"ERROR: {e}", file=sys.stderr)
        raise SystemExit(1) from e



