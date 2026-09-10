#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""认证环境变量加载：优先使用本机 Windows 系统 / 进程环境变量。

优先级（高 → 低）:
  1) 操作系统环境变量（User / Machine / 进程已有）
  2) 可选本地文件（仅补齐空缺，不覆盖系统变量）:
       <skill>/config.local.env
       <skill>/.env.local
       <skill>/.env

规则:
  - 默认不在 Skill 目录存放真实账号密码；推荐在系统环境变量中配置
  - 若仍存在本地文件，其中的键仅在对应环境变量为空时写入
  - 禁止把含真实密码的 config.local.env 提交到仓库
"""
from __future__ import annotations

import os
from pathlib import Path

_SKILL_ROOT = Path(__file__).resolve().parent.parent
_CANDIDATES = (
    _SKILL_ROOT / "config.local.env",
    _SKILL_ROOT / ".env.local",
    _SKILL_ROOT / ".env",
)

_LOADED_FROM: str | None = None
_SYSTEM_ENV_MERGED = False

# 脚本关心的认证相关键（从 Windows User/Machine 环境补进当前进程）
_AUTH_KEYS = (
    "JIRA_USERNAME",
    "JIRA_PASSWORD",
    "JIRA_USERNAME",
    "JIRA_PASSWORD",
    "JIRA_EMAIL",
    "JIRA_API_TOKEN",
    "JIRA_COOKIE",
    "CONFLUENCE_COOKIE",
    "FIGMA_TOKEN",
    "TEAM_KB_URL",
    "TEAM_KB_TIMEOUT",
)


def skill_root() -> Path:
    return _SKILL_ROOT


def _merge_windows_system_env() -> None:
    """把本机 User/Machine 级系统变量合并进 os.environ（不覆盖进程已有非空值）。"""
    global _SYSTEM_ENV_MERGED
    if _SYSTEM_ENV_MERGED:
        return
    _SYSTEM_ENV_MERGED = True
    if os.name != "nt":
        return
    try:
        import winreg
    except ImportError:
        return

    roots = (
        (winreg.HKEY_CURRENT_USER, r"Environment"),
        (
            winreg.HKEY_LOCAL_MACHINE,
            r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment",
        ),
    )
    for hive, subkey in roots:
        try:
            with winreg.OpenKey(hive, subkey) as key:
                i = 0
                while True:
                    try:
                        name, value, _ = winreg.EnumValue(key, i)
                    except OSError:
                        break
                    i += 1
                    if name not in _AUTH_KEYS:
                        continue
                    if value is None:
                        continue
                    text = str(value).strip()
                    if not text:
                        continue
                    if not os.environ.get(name, "").strip():
                        os.environ[name] = text
        except OSError:
            continue


def _parse_env_file(path: Path) -> dict[str, str]:
    data: dict[str, str] = {}
    text = path.read_text(encoding="utf-8-sig")
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[7:].strip()
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        if not key:
            continue
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
            value = value[1:-1]
        data[key] = value
    return data


def load_local_env(prefer_local: bool = False) -> str | None:
    """合并系统环境变量，并可选从本地文件补齐空缺项。

    Args:
        prefer_local: False（默认）时，系统/进程环境变量优先，本地文件仅填充空缺；
            True 时本地文件覆盖已有同名变量（不推荐）。

    Returns:
        实际加载的本地文件路径字符串；未使用本地文件则返回 None。
    """
    global _LOADED_FROM
    _merge_windows_system_env()

    chosen: Path | None = None
    for path in _CANDIDATES:
        if path.is_file():
            chosen = path
            break
    if chosen is None:
        return None

    parsed = _parse_env_file(chosen)
    for key, value in parsed.items():
        if prefer_local or key not in os.environ or os.environ.get(key, "") == "":
            os.environ[key] = value
    _LOADED_FROM = str(chosen)
    return _LOADED_FROM


def ensure_local_env(prefer_local: bool = False) -> str | None:
    """幂等加载：重复调用只解析一次；系统环境每次确保已合并。"""
    _merge_windows_system_env()
    if _LOADED_FROM:
        return _LOADED_FROM
    return load_local_env(prefer_local=prefer_local)


# 被 import 时即尝试加载，便于各脚本只需一行 import
ensure_local_env()
