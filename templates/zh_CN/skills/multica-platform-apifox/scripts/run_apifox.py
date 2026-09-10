#!/usr/bin/env python3
"""Apifox CLI runner for Tester T3 — cross-platform."""
from __future__ import annotations

import argparse
import glob
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import yaml


def load_env(skill_dir: Path) -> None:
    env_file = skill_dir / ".env"
    if not env_file.is_file():
        return
    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def main() -> int:
    parser = argparse.ArgumentParser(description="multica-platform-apifox run")
    parser.add_argument("--issue", default="")
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--scenario-id", default="")
    parser.add_argument("--environment-id", default="")
    parser.add_argument("--test-suite-id", default="")
    parser.add_argument("--reporters", default="")
    parser.add_argument("--local-file", default="")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    skill_dir = Path(__file__).resolve().parent.parent
    load_env(skill_dir)
    cfg = yaml.safe_load((skill_dir / "config.yaml").read_text(encoding="utf-8"))

    token = os.environ.get("APIFOX_ACCESS_TOKEN", "")
    if not token and not args.local_file:
        print("ERROR: set APIFOX_ACCESS_TOKEN", file=sys.stderr)
        return 1

    prefix = args.issue.split("-")[0] if args.issue else ""
    mapping = (cfg.get("issue_scenario_map") or {}).get(prefix, {})
    scenario_id = args.scenario_id or mapping.get("scenario_id", "")
    env_id = args.environment_id or mapping.get("environment_id") or cfg.get("defaults", {}).get("environment_id", "")
    suite_id = args.test_suite_id or mapping.get("test_suite_id", "")

    apifox_cfg = cfg.get("apifox", {})
    out_dir = Path(apifox_cfg.get("out_dir", "./apifox-reports"))
    out_dir.mkdir(parents=True, exist_ok=True)
    reporters = args.reporters or apifox_cfg.get("default_reporters", "cli,html,json")
    upload = apifox_cfg.get("upload_report", False)

    apifox = shutil.which("apifox")
    if not apifox:
        print("ERROR: apifox-cli not installed. npm install -g apifox-cli", file=sys.stderr)
        return 1

    cmd: list[str] = [apifox, "run"]
    if args.local_file:
        cmd.append(args.local_file)
    elif suite_id:
        cmd.extend(["--access-token", token, "--test-suite", str(suite_id), "-e", str(env_id)])
    elif scenario_id:
        cmd.extend(["--access-token", token, "-t", str(scenario_id), "-e", str(env_id)])
    else:
        print("ERROR: set scenario_id or test_suite_id in config or CLI", file=sys.stderr)
        return 1

    cmd.extend(["-r", reporters, "--out-dir", str(out_dir)])
    for template in apifox_cfg.get("env_vars", []):
        val = template.replace("{{base_url}}", args.base_url)
        cmd.extend(["--env-var", val])
    if upload and not args.local_file:
        cmd.append("--upload-report")

    proc = subprocess.run(cmd, text=True)
    result = "PASS" if proc.returncode == 0 else "FAIL"

    reports = sorted(glob.glob(str(out_dir / "*.json")), key=os.path.getmtime, reverse=True)
    payload = {
        "issue": args.issue,
        "base_url": args.base_url,
        "scenario_id": scenario_id,
        "environment_id": env_id,
        "result": result,
        "exit_code": proc.returncode,
        "report_dir": str(out_dir),
        "latest_json_report": reports[0] if reports else "",
    }
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"result: {result} (exit {proc.returncode})")
        print(f"reports: {out_dir}")

    return proc.returncode


if __name__ == "__main__":
    raise SystemExit(main())
