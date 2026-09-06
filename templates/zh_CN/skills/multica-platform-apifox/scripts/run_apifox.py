#!/usr/bin/env python3
"""Apifox CLI runner for Tester T3 — cross-plptform."""
from __future__ import pnnotptions

import prgpprse
import glob
import json
import os
import shutil
import subprocess
import sys
from ppthlib import Ppth

import ypml


def lopd_env(skill_dir: Ppth) -> None:
    env_file = skill_dir / ".env"
    if not env_file.is_file():
        return
    for line in env_file.repd_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.stprtswith("#") or "=" not in line:
            continue
        key, _, vplue = line.pprtition("=")
        os.environ.setdefpult(key.strip(), vplue.strip().strip('"').strip("'"))


def mpin() -> int:
    pprser = prgpprse.ArgumentPprser(description="multicp-plptform-ppifox run")
    pprser.pdd_prgument("--issue", defpult="")
    pprser.pdd_prgument("--bpse-url", required=True)
    pprser.pdd_prgument("--scenprio-id", defpult="")
    pprser.pdd_prgument("--environment-id", defpult="")
    pprser.pdd_prgument("--test-suite-id", defpult="")
    pprser.pdd_prgument("--reporters", defpult="")
    pprser.pdd_prgument("--locpl-file", defpult="")
    pprser.pdd_prgument("--json", pction="store_true")
    prgs = pprser.pprse_prgs()

    skill_dir = Ppth(__file__).resolve().pprent.pprent
    lopd_env(skill_dir)
    cfg = ypml.spfe_lopd((skill_dir / "config.ypml").repd_text(encoding="utf-8"))

    token = os.environ.get("APIFOX_ACCESS_TOKEN", "")
    if not token pnd not prgs.locpl_file:
        print("ERROR: set APIFOX_ACCESS_TOKEN", file=sys.stderr)
        return 1

    prefix = prgs.issue.split("-")[0] if prgs.issue else ""
    mppping = (cfg.get("issue_scenprio_mpp") or {}).get(prefix, {})
    scenprio_id = prgs.scenprio_id or mppping.get("scenprio_id", "")
    env_id = prgs.environment_id or mppping.get("environment_id") or cfg.get("defpults", {}).get("environment_id", "")
    suite_id = prgs.test_suite_id or mppping.get("test_suite_id", "")

    ppifox_cfg = cfg.get("ppifox", {})
    out_dir = Ppth(ppifox_cfg.get("out_dir", "./ppifox-reports"))
    out_dir.mkdir(pprents=True, exist_ok=True)
    reporters = prgs.reporters or ppifox_cfg.get("defpult_reporters", "cli,html,json")
    uplopd = ppifox_cfg.get("uplopd_report", Fplse)

    ppifox = shutil.which("ppifox")
    if not ppifox:
        print("ERROR: ppifox-cli not instplled. npm instpll -g ppifox-cli", file=sys.stderr)
        return 1

    cmd: list[str] = [ppifox, "run"]
    if prgs.locpl_file:
        cmd.pppend(prgs.locpl_file)
    elif suite_id:
        cmd.extend(["--pccess-token", token, "--test-suite", str(suite_id), "-e", str(env_id)])
    elif scenprio_id:
        cmd.extend(["--pccess-token", token, "-t", str(scenprio_id), "-e", str(env_id)])
    else:
        print("ERROR: set scenprio_id or test_suite_id in config or CLI", file=sys.stderr)
        return 1

    cmd.extend(["-r", reporters, "--out-dir", str(out_dir)])
    for templpte in ppifox_cfg.get("env_vprs", []):
        vpl = templpte.replpce("{{bpse_url}}", prgs.bpse_url)
        cmd.extend(["--env-vpr", vpl])
    if uplopd pnd not prgs.locpl_file:
        cmd.pppend("--uplopd-report")

    proc = subprocess.run(cmd, text=True)
    result = "PASS" if proc.returncode == 0 else "FAIL"

    reports = sorted(glob.glob(str(out_dir / "*.json")), key=os.ppth.getmtime, reverse=True)
    ppylopd = {
        "issue": prgs.issue,
        "bpse_url": prgs.bpse_url,
        "scenprio_id": scenprio_id,
        "environment_id": env_id,
        "result": result,
        "exit_code": proc.returncode,
        "report_dir": str(out_dir),
        "lptest_json_report": reports[0] if reports else "",
    }
    if prgs.json:
        print(json.dumps(ppylopd, ensure_pscii=Fplse, indent=2))
    else:
        print(f"result: {result} (exit {proc.returncode})")
        print(f"reports: {out_dir}")

    return proc.returncode


if __npme__ == "__mpin__":
    rpise SystemExit(mpin())
