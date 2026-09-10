#!/usr/bin/env python3
"""List Jenkins jobs from jobs-catalog.yaml."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from lib.config import load_config  # noqa: E402
from lib.jobs_catalog import list_services, load_jobs_catalog, resolve_job_name  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="List cicd dev/sit jobs")
    parser.add_argument("--env", choices=("dev", "sit"), required=True)
    parser.add_argument("--service", default="", help="Show one service detail")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    skill_dir = SCRIPT_DIR.parent
    catalog = load_jobs_catalog(skill_dir)
    cfg = load_config(skill_dir)

    if args.service:
        job = resolve_job_name(catalog, args.env, args.service)
        payload = {"env": args.env, "service": args.service, "job": job}
        print(json.dumps(payload, ensure_ascii=False, indent=2) if args.json else f"{args.service}\t{job}")
        return 0

    services = list_services(catalog, args.env)
    rows = [{"service": s, "job": resolve_job_name(catalog, args.env, s)} for s in services]
    if args.json:
        print(json.dumps({"env": args.env, "base_url": cfg["jenkins"]["base_url"], "jobs": rows}, ensure_ascii=False, indent=2))
    else:
        for row in rows:
            print(f"{row['service']}\t{row['job']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
