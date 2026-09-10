#!/usr/bin/env python3
"""Backward-compatible alias: trigger SIT jobs via trigger_env.py."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent


def main() -> int:
    # Delegate to trigger_env; BUILD_SIT_PROJECTS → --service
    import os

    args = [sys.executable, str(SCRIPT_DIR / "trigger_env.py"), "--env", "sit"]
    args.extend(sys.argv[1:])
    if "BUILD_SIT_PROJECTS" in os.environ and "--service" not in " ".join(sys.argv):
        for svc in os.environ["BUILD_SIT_PROJECTS"].split():
            if svc.strip():
                args.extend(["--service", svc.strip()])
    return subprocess.run(args, check=False).returncode


if __name__ == "__main__":
    raise SystemExit(main())
