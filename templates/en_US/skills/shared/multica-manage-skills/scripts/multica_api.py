#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
multica_api.py — multica 平台 API 客户端（workspace / agent 统计）

纯标准库实现（urllib），无第三方依赖，Windows / Linux / macOS 通用。
用于随时查询已部署 multica 服务的 API 信息（workspace 列表、agent 运行次数、活动明细等）。

认证（token）解析，从高到低:
  1. --token 参数
  2. 环境变量 MULTICA_API_TOKEN
  （token 在 UI 的 Settings -> Access Tokens 创建，形如 mul_xxx）

API 地址解析，从高到低:
  1. --url 参数
  2. 环境变量 MULTICA_API_URL
  3. 默认 <MULTICA_API_URL>

重要: 本脚本不读取任何本地配置文件（不读 ~/.multica/config.json，
也不读脚本目录下的 config.json），只接受命令行参数和环境变量，
避免本地文件干扰。

用法示例:
  python multica_api.py me
  python multica_api.py workspaces
  python multica_api.py agents --workspace 1
  python multica_api.py run-counts --workspace 1 --json
  python multica_api.py activity --workspace 1
  python multica_api.py report                        # 所有 workspace 汇总
  python multica_api.py report --workspace 1          # 单个 workspace 的 agent 明细
"""

import argparse
import csv
import io
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

DEFAULT_BASE_URL = "<MULTICA_API_URL>"
TIMEOUT = 30


class MulticaError(Exception):
    """API 调用失败（HTTP 错误、网络错误、鉴权失败等）。"""


def _utf8_stdout():
    """Windows 控制台默认 gbk，改成 utf-8 避免中文/emoji 乱码。"""
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


def resolve_base_url(args_url):
    return (args_url or os.environ.get("MULTICA_API_URL") or DEFAULT_BASE_URL).rstrip("/")


def resolve_token(args_token):
    return args_token or os.environ.get("MULTICA_API_TOKEN") or ""


class MulticaClient:
    """多工作区 multica API 客户端。

    workspace 参数可传 slug（如 "1"、"my-team"）或 workspace UUID，
    通过 X-Workspace-Slug 请求头传递，服务端两者都能解析。
    """

    def __init__(self, base_url, token):
        self.base_url = base_url
        self.token = token
        self._headers = {
            "Accept": "application/json",
            "X-Client-Platform": "cli",
            "X-Client-Version": "dev",
        }

    # ------------------------------------------------------------------
    # 底层请求
    # ------------------------------------------------------------------
    def _request(self, method, path, workspace=None, params=None):
        url = self.base_url + path
        if params:
            url += ("&" if "?" in url else "?") + urllib.parse.urlencode(params)
        headers = dict(self._headers)
        if workspace:
            headers["X-Workspace-Slug"] = str(workspace)
        if self.token:
            headers["Authorization"] = "Bearer " + self.token
        req = urllib.request.Request(url, method=method, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
                body = resp.read().decode("utf-8")
                return json.loads(body) if body else None
        except urllib.error.HTTPError as e:
            detail = ""
            try:
                detail = e.read().decode("utf-8", "replace")[:500]
            except Exception:
                pass
            hint = ""
            if e.code in (401, 403):
                hint = "（token 无效或权限不足：用 --token 参数或设置环境变量 MULTICA_API_TOKEN）"
            raise MulticaError(f"HTTP {e.code} {e.reason} — {url}{hint}\n{detail}")
        except urllib.error.URLError as e:
            raise MulticaError(f"网络错误 — {url}: {e.reason}")

    # ------------------------------------------------------------------
    # 端点封装
    # ------------------------------------------------------------------
    def get_me(self):
        """当前登录用户信息。"""
        return self._request("GET", "/api/me")

    def list_workspaces(self):
        """当前用户可见的所有 workspace（id / name / slug / created_at...）。"""
        return self._request("GET", "/api/workspaces")

    def list_agents(self, workspace):
        """workspace 内 agent 列表（id / name / runtime_mode...）。"""
        return self._request("GET", "/api/agents", workspace=workspace)

    def agent_run_counts(self, workspace):
        """workspace 内每个 agent 的 30 天运行次数: [{agent_id, run_count}]。"""
        return self._request("GET", "/api/agent-run-counts", workspace=workspace)

    def agent_activity_30d(self, workspace):
        """workspace 内每个 agent 的 30 天日活明细:
        [{agent_id, bucket_at, task_count, failed_count}]（bucket_at 为 UTC 当日 0 点）。"""
        return self._request("GET", "/api/agent-activity-30d", workspace=workspace)

    # ------------------------------------------------------------------
    # 汇总
    # ------------------------------------------------------------------
    def workspace_report(self, workspace):
        """合并 run-counts + activity + agents，得到每个 agent 的统计明细。

        以 agents 列表为基底（保证 0 运行的 agent 也出现在结果里），
        再叠加 30 天运行次数与日活明细。
        """
        agents, runs, activity = [], [], []
        for method, target in (
            (self.list_agents, agents),
            (self.agent_run_counts, runs),
            (self.agent_activity_30d, activity),
        ):
            try:
                target.extend(method(workspace) or [])
            except MulticaError as e:
                print(f"  [warn] {e}", file=sys.stderr)

        name_map = {a.get("id"): (a.get("name") or "?") for a in agents}
        per = {}

        def _entry(aid):
            return dict(agent_id=aid, agent_name=name_map.get(aid, aid[:8] if aid else "?"),
                        run_count=0, task_count=0, failed_count=0, fail_rate=0.0)

        for a in agents:
            aid = a.get("id")
            if aid:
                per[aid] = _entry(aid)
        for r in runs:
            aid = r.get("agent_id")
            if aid:
                per.setdefault(aid, _entry(aid))["run_count"] = int(r.get("run_count") or 0)
        for a in activity:
            aid = a.get("agent_id")
            if aid:
                e = per.setdefault(aid, _entry(aid))
                e["task_count"] += int(a.get("task_count") or 0)
                e["failed_count"] += int(a.get("failed_count") or 0)
        rows = list(per.values())
        for e in rows:
            tc = e["task_count"]
            e["fail_rate"] = round(100.0 * e["failed_count"] / tc, 1) if tc else 0.0
        rows.sort(key=lambda x: x["run_count"], reverse=True)
        return rows


# ----------------------------------------------------------------------
# 输出
# ----------------------------------------------------------------------
def _print_table(headers, rows):
    def cell(x):
        return " ".join(str(x).split())

    headers = [cell(h) for h in headers]
    cells = [[cell(c) for c in row] for row in rows]
    widths = [len(h) for h in headers]
    for row in cells:
        for i, c in enumerate(row):
            widths[i] = max(widths[i], len(c))
    print("  ".join(h.ljust(widths[i]) for i, h in enumerate(headers)))
    print("  ".join("-" * w for w in widths))
    for row in cells:
        print("  ".join(c.ljust(widths[i]) for i, c in enumerate(row)))


def _emit(data, as_json, as_csv, printer=None, csv_headers=None, csv_rows=None):
    if as_json:
        print(json.dumps(data, ensure_ascii=False, indent=2))
    elif as_csv:
        if csv_headers is None or csv_rows is None:
            raise MulticaError("该命令不支持 --csv")
        buf = io.StringIO()
        w = csv.writer(buf)
        w.writerow(csv_headers)
        w.writerows(csv_rows)
        print(buf.getvalue().rstrip())
    elif printer is not None:
        printer(data)
    else:
        raise MulticaError("缺少输出方式")


# ----------------------------------------------------------------------
# 各子命令的打印逻辑
# ----------------------------------------------------------------------
def _print_workspaces(data):
    if not data:
        print("（无 workspace）")
        return
    _print_table(
        ["ID", "NAME", "SLUG", "CREATED_AT"],
        [[w["id"], w.get("name") or "", w.get("slug") or "", (w.get("created_at") or "")[:19]] for w in data],
    )


def _print_agents(data):
    if not data:
        print("（无 agent）")
        return
    _print_table(
        ["AGENT_ID", "NAME", "RUNTIME_MODE"],
        [[a["id"], a.get("name") or "", a.get("runtime_mode") or ""] for a in data],
    )


def _print_run_counts(data):
    if not data:
        print("（30 天内无运行）")
        return
    _print_table(["AGENT_ID", "RUN_COUNT"], [[r["agent_id"], r.get("run_count", 0)] for r in data])


def _print_activity(data):
    if not data:
        print("（30 天内无活动）")
        return
    _print_table(
        ["AGENT_ID", "BUCKET_AT", "TASK_COUNT", "FAILED_COUNT"],
        [[a["agent_id"], (a.get("bucket_at") or "")[:10], a.get("task_count", 0), a.get("failed_count", 0)]
         for a in sorted(data, key=lambda x: x.get("bucket_at") or "")],
    )


def _print_report(rows):
    if not rows:
        print("（无数据）")
        return
    _print_table(
        ["AGENT_NAME", "AGENT_ID", "RUN_COUNT_30D", "TASK_COUNT_30D", "FAILED_COUNT", "FAIL_RATE"],
        [[r["agent_name"], r["agent_id"], r["run_count"], r["task_count"], r["failed_count"],
          f'{r["fail_rate"]}%'] for r in rows],
    )


def _print_report_summary(rows):
    if not rows:
        print("（无 workspace）")
        return
    _print_table(
        ["WORKSPACE", "SLUG", "AGENTS", "RUNS_30D", "TASKS_30D", "FAILED"],
        [[r["workspace_name"], r["workspace_slug"], r["agent_count"], r["run_count_30d"],
          r["task_count_30d"], r["failed_count"]] for r in rows],
    )


# ----------------------------------------------------------------------
# CLI
# ----------------------------------------------------------------------
def build_parser():
    p = argparse.ArgumentParser(
        prog="multica_api",
        description="multica 平台 API 查询工具（workspace / agent 统计）。"
                    "用法: multica_api <子命令> --workspace <slug|id>",
    )
    p.add_argument("--url", help="API 地址（默认: env MULTICA_API_URL / ~/.multica/config.json / <MULTICA_API_URL>）")
    p.add_argument("--token", help="API token（mul_ 开头），优先级高于 env 与 CLI 配置")
    p.add_argument("--workspace", help="workspace slug 或 UUID（agents / run-counts / activity / report 使用）")
    p.add_argument("--json", action="store_true", help="JSON 输出")
    p.add_argument("--csv", action="store_true", help="CSV 输出")
    sub = p.add_subparsers(dest="cmd", metavar="子命令", required=True)

    def add(name, help_text):
        sp = sub.add_parser(name, help=help_text)
        # dest 与默认值用 SUPPRESS，避免子命令覆盖全局 --workspace/--json/--csv
        sp.add_argument("--workspace", dest="sub_workspace", default=argparse.SUPPRESS,
                        help="workspace slug 或 UUID（覆盖全局）")
        sp.add_argument("--json", dest="sub_json", action="store_true", default=argparse.SUPPRESS,
                        help="JSON 输出")
        sp.add_argument("--csv", dest="sub_csv", action="store_true", default=argparse.SUPPRESS,
                        help="CSV 输出")

    add("me", "显示当前登录用户信息")
    add("workspaces", "列出当前用户可见的所有 workspace")
    add("agents", "列出某 workspace 的 agents")
    add("run-counts", "某 workspace 每个 agent 的 30 天运行次数")
    add("activity", "某 workspace 每个 agent 的 30 天日活明细")
    add("report", "统计汇总（默认所有 workspace；--workspace 指定单个则输出 agent 明细）")
    return p


def main(argv=None):
    _utf8_stdout()
    args = build_parser().parse_args(argv)
    client = MulticaClient(resolve_base_url(getattr(args, "url", None)),
                           resolve_token(getattr(args, "token", None)))

    cmd = args.cmd
    workspace = getattr(args, "sub_workspace", None) or getattr(args, "workspace", None)
    as_json = getattr(args, "sub_json", False) or getattr(args, "json", False)
    as_csv = getattr(args, "sub_csv", False) or getattr(args, "csv", False)

    try:
        if cmd == "me":
            _emit(client.get_me(), as_json, as_csv, printer=print)

        elif cmd == "workspaces":
            data = client.list_workspaces()
            _emit(data, as_json, as_csv,
                  printer=_print_workspaces,
                  csv_headers=["id", "name", "slug", "created_at"],
                  csv_rows=[[w["id"], w.get("name") or "", w.get("slug") or "", w.get("created_at") or ""]
                            for w in data])

        elif cmd == "agents":
            if not workspace:
                raise MulticaError("缺少 --workspace <slug|id>")
            data = client.list_agents(workspace)
            _emit(data, as_json, as_csv,
                  printer=_print_agents,
                  csv_headers=["agent_id", "name", "runtime_mode"],
                  csv_rows=[[a["id"], a.get("name") or "", a.get("runtime_mode") or ""] for a in data])

        elif cmd == "run-counts":
            if not workspace:
                raise MulticaError("缺少 --workspace <slug|id>")
            data = client.agent_run_counts(workspace)
            _emit(data, as_json, as_csv,
                  printer=_print_run_counts,
                  csv_headers=["agent_id", "run_count"],
                  csv_rows=[[r["agent_id"], r.get("run_count", 0)] for r in data])

        elif cmd == "activity":
            if not workspace:
                raise MulticaError("缺少 --workspace <slug|id>")
            data = client.agent_activity_30d(workspace)
            _emit(data, as_json, as_csv,
                  printer=_print_activity,
                  csv_headers=["agent_id", "bucket_at", "task_count", "failed_count"],
                  csv_rows=[[a["agent_id"], (a.get("bucket_at") or "")[:10], a.get("task_count", 0),
                             a.get("failed_count", 0)] for a in data])

        elif cmd == "report":
            if workspace:
                rows = client.workspace_report(workspace)
                _emit(rows, as_json, as_csv,
                      printer=_print_report,
                      csv_headers=["agent_name", "agent_id", "run_count_30d", "task_count_30d",
                                   "failed_count", "fail_rate"],
                      csv_rows=[[r["agent_name"], r["agent_id"], r["run_count"], r["task_count"],
                                 r["failed_count"], r["fail_rate"]] for r in rows])
            else:
                ws_list = client.list_workspaces()
                if not ws_list:
                    print("（无 workspace）")
                    return
                summary = []
                for w in ws_list:
                    rows = client.workspace_report(w["slug"])
                    summary.append({
                        "workspace_id": w["id"],
                        "workspace_name": w.get("name") or "",
                        "workspace_slug": w.get("slug") or "",
                        "agent_count": len(rows),
                        "run_count_30d": sum(r["run_count"] for r in rows),
                        "task_count_30d": sum(r["task_count"] for r in rows),
                        "failed_count": sum(r["failed_count"] for r in rows),
                    })
                _emit(summary, as_json, as_csv,
                      printer=_print_report_summary,
                      csv_headers=["workspace_name", "workspace_slug", "agent_count", "run_count_30d",
                                   "task_count_30d", "failed_count"],
                      csv_rows=[[s["workspace_name"], s["workspace_slug"], s["agent_count"], s["run_count_30d"],
                                 s["task_count_30d"], s["failed_count"]] for s in summary])
    except MulticaError as e:
        print(f"错误: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

