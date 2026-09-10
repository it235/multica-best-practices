#!/usr/bin/env python3
"""Jenkins platform CLI — cross-platform (Windows / Linux)."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from lib.config import load_config  # noqa: E402
from lib.jenkins_client import JenkinsError  # noqa: E402
from lib.jobs_catalog import job_api_path, load_jobs_catalog, resolve_job_name  # noqa: E402
from lib.param_discovery import ParameterDiscovery, resolve_trigger_params  # noqa: E402
from lib import make_client  # noqa: E402


def _overrides_from_args(param_list: list[str]) -> dict[str, str]:
    out: dict[str, str] = {}
    for p in param_list:
        if "=" in p:
            k, v = p.split("=", 1)
            out[k] = v
    return out


def _resolve_job_path(args: argparse.Namespace) -> str:
    if args.job_path:
        return args.job_path
    if args.service:
        catalog = load_jobs_catalog(SCRIPT_DIR.parent)
        job_name = resolve_job_name(catalog, args.env, args.service)
        return job_api_path(job_name)
    raise SystemExit("ERROR: specify --job-path or --service")


def cmd_discover_params(args: argparse.Namespace) -> int:
    client = make_client()
    job_path = _resolve_job_path(args)
    overrides = _overrides_from_args(args.param)
    discovery = ParameterDiscovery(client).discover(
        job_path,
        branch=args.branch,
        env=args.env,
        service=args.service,
        issue_key=args.issue,
        overrides=overrides,
        use_last_success=not args.no_last_success,
    )
    print(json.dumps(discovery, ensure_ascii=False, indent=2))
    return 0 if discovery.get("ready", True) else 2


def cmd_trigger_wait(args: argparse.Namespace) -> int:
    client = make_client()
    job_path = _resolve_job_path(args)
    overrides = _overrides_from_args(args.param)
    if args.auto_params:
        params = resolve_trigger_params(
            client,
            job_path,
            branch=args.branch,
            env=args.env,
            service=args.service,
            overrides=overrides,
            strict=not args.allow_missing,
            use_last_success=not args.no_last_success,
        )
    else:
        params = overrides

    if args.timeout_seconds:
        client.timeout = args.timeout_seconds
    if args.poll_interval_seconds:
        client.poll_interval = args.poll_interval_seconds

    data = client.trigger_and_wait(job_path, params)
    out = {
        "url": data.get("url", ""),
        "number": data.get("number"),
        "result": data.get("result"),
        "displayName": data.get("fullDisplayName", ""),
        "params_used": params,
    }
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


def cmd_build_info(args: argparse.Namespace) -> int:
    client = make_client()
    url = f"{client.job_url(args.job_path)}/{args.build}/api/json"
    _, _, body = client._request("GET", url)  # noqa: SLF001
    print(body.decode("utf-8"))
    return 0


def cmd_console(args: argparse.Namespace) -> int:
    client = make_client()
    text = client.console_tail(args.job_path, args.build, args.tail)
    print(text)
    return 0


def cmd_last_success(args: argparse.Namespace) -> int:
    client = make_client()
    cfg = load_config(SCRIPT_DIR.parent)
    legacy = (cfg.get("legacy_profiles") or {}).get(args.profile, {})
    job_path = args.job_path or legacy.get("job_path", "")
    if not job_path:
        raise SystemExit("ERROR: --job-path required (legacy profile optional)")
    build = client.last_success(job_path, args.project or "")
    print(json.dumps(build, ensure_ascii=False))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="multica-platform-jenkins CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    for p in (
        sub.add_parser("discover-params", help="Fetch job parameters from Jenkins API"),
        sub.add_parser("trigger-wait", help="Trigger build and wait SUCCESS"),
    ):
        p.add_argument("--job-path", default="")
        p.add_argument("--env", choices=("dev", "sit"), default="sit")
        p.add_argument("--service", default="")
        p.add_argument("--branch", default="")
        p.add_argument("--issue", default="")
        p.add_argument("--param", action="append", default=[], help="Override key=value")

    p_disc = sub.choices["discover-params"]
    p_disc.add_argument("--no-last-success", action="store_true")
    p_disc.set_defaults(func=cmd_discover_params)

    p_tw = sub.choices["trigger-wait"]
    p_tw.add_argument("--no-last-success", action="store_true")
    p_tw.add_argument("--auto-params", action="store_true", default=True)
    p_tw.add_argument("--no-auto-params", action="store_false", dest="auto_params")
    p_tw.add_argument("--allow-missing", action="store_true", help="Skip strict missing check")
    p_tw.add_argument("--timeout-seconds", type=int)
    p_tw.add_argument("--poll-interval-seconds", type=int)
    p_tw.set_defaults(func=cmd_trigger_wait)

    p_bi = sub.add_parser("build-info")
    p_bi.add_argument("--job-path", required=True)
    p_bi.add_argument("--build", type=int, required=True)
    p_bi.set_defaults(func=cmd_build_info)

    p_co = sub.add_parser("console")
    p_co.add_argument("--job-path", required=True)
    p_co.add_argument("--build", type=int, required=True)
    p_co.add_argument("--tail", type=int, default=200)
    p_co.set_defaults(func=cmd_console)

    p_ls = sub.add_parser("last-success")
    p_ls.add_argument("--profile", choices=("sit", "prod"), default="sit")
    p_ls.add_argument("--job-path", default="")
    p_ls.add_argument("--project", default="")
    p_ls.set_defaults(func=cmd_last_success)

    args = parser.parse_args()
    try:
        return args.func(args)
    except JenkinsError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
