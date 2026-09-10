"""Shared helpers to build JenkinsClient from skill config."""
from __future__ import annotations

import os
from pathlib import Path

from lib.config import load_config
from lib.credentials import load_skill_env, resolve_jenkins_credentials
from lib.jenkins_client import JenkinsClient


def skill_dir_from_here() -> Path:
    return Path(__file__).resolve().parent.parent


def make_client(skill_dir: Path | None = None) -> JenkinsClient:
    skill_dir = skill_dir or skill_dir_from_here()
    load_skill_env(skill_dir)
    user, password = resolve_jenkins_credentials()
    cfg = load_config(skill_dir)
    jenkins_cfg = cfg.get("jenkins", {})
    base_url = os.environ.get("JENKINS_URL") or jenkins_cfg.get("base_url", "")
    curl_resolve = os.environ.get("JENKINS_CURL_RESOLVE") or jenkins_cfg.get("curl_resolve") or ""
    timeout = int(os.environ.get("TIMEOUT_SECONDS") or jenkins_cfg.get("timeout_seconds") or 1800)
    poll = int(os.environ.get("POLL_INTERVAL_SECONDS") or jenkins_cfg.get("poll_interval_seconds") or 5)
    return JenkinsClient(base_url, user, password, curl_resolve, timeout, poll)
