#!/usr/bin/env python3
"""
Dedup Check - 与 Jira 已有用例对比去重。

用法:
  python scripts/dedup_check.py \\
    --jira-url https://your-domain.atlassian.net/browse/PROJ-123 \\
    --input proposed_test_cases.json \\
    --output deduped_test_cases.json

功能:
  1. 拉取 Jira 需求下已有的测试用例（子任务/关联 issue）
  2. 对每个新用例，按标题+步骤与已有用例做模糊匹配
  3. 标记重复项并给出相似度分数
  4. 输出去重后的用例列表

环境变量:
  JIRA_EMAIL, JIRA_API_TOKEN  - Cloud Jira 认证
  JIRA_COOKIE                 - 自部署 Jira 认证（如 JSESSIONID=xxx）
"""

import argparse
import json
import os
import re
import sys
# Fix Windows terminal encoding for Chinese output
if sys.platform == 'win32' and hasattr(sys.stdout, 'buffer'):
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from base64 import b64encode
from difflib import SequenceMatcher
from urllib.parse import urlparse

try:
    import local_env  # noqa: F401  — 加载 config.local.env
except ImportError:
    pass

try:
    import requests
except ImportError:
    print('缺少 requests 库，请执行: pip install requests', file=sys.stderr)
    sys.exit(1)


# ============================================================
# JQL / API Constants
# ============================================================

# 常见的测试用例 issue 类型名称
TEST_ISSUE_TYPES = {"Test", "测试用例", "测试", "Sub-test", "Subtask", "子任务"}


# ============================================================
# Auth & API
# ============================================================

def get_rest_path() -> str:
    return "/rest/api/2" if ("JIRA_COOKIE" in os.environ or "JIRA_USERNAME" in os.environ) else "/rest/api/3"


def build_auth_headers() -> dict:
    """根据环境变量自动选择认证方式（优先使用用户名密码，防止 cookie 过期）"""
    headers = {"Accept": "application/json"}

    username = os.environ.get("JIRA_USERNAME")
    password = os.environ.get("JIRA_PASSWORD")
    if username and password:
        b = b64encode(f"{username}:{password}".encode()).decode()
        headers["Authorization"] = f"Basic {b}"
        return headers

    email = os.environ.get("JIRA_EMAIL")
    api_token = os.environ.get("JIRA_API_TOKEN")
    if email and api_token:
        b = b64encode(f"{email}:{api_token}".encode()).decode()
        headers["Authorization"] = f"Basic {b}"
        return headers

    cookie = os.environ.get("JIRA_COOKIE")
    if cookie:
        headers["Cookie"] = cookie
        return headers

    print(
        "请配置认证（优先 Windows 系统环境变量 JIRA_USERNAME/PASSWORD 或 JIRA_USERNAME / JIRA_PASSWORD；可选 config.local.env 兜底）:\n"
        "  复制 config.local.env.example → config.local.env 并填写",
        file=sys.stderr,
    )
    sys.exit(1)


def parse_jira_url(url: str) -> tuple[str, str]:
    parsed = urlparse(url)
    base = f"{parsed.scheme}://{parsed.netloc}"
    m = re.search(r'/browse/([A-Z]+-\d+)', parsed.path)
    if not m:
        raise ValueError(f"无法解析 Jira URL: {url}")
    return base, m.group(1)


def jira_get(base: str, path: str, auth: dict) -> dict:
    """请求 Jira API，自动适配 /rest/api/2 或 /rest/api/3"""
    rest_path = get_rest_path()
    url = f"{base}{rest_path}{path}" if not path.startswith("/rest/") else f"{base}{path}"
    resp = requests.get(url, headers=auth, timeout=30)
    if resp.status_code == 401:
        print("认证失败：请检查 JIRA_USERNAME+JIRA_PASSWORD 或 JIRA_COOKIE 或 JIRA_EMAIL+JIRA_API_TOKEN", file=sys.stderr)
        sys.exit(1)
    resp.raise_for_status()
    return resp.json()


# ============================================================
# 拉取已有测试用例
# ============================================================

def fetch_existing_test_cases(base_url: str, parent_key: str, auth: dict) -> list[dict]:
    """
    通过 JQL 查询该需求下所有子任务 / 关联 issue 中的测试用例。
    策略：
      1. 查询 parent = parent_key 的子任务
      2. 查询 issueLink 关联到 parent_key 且类型为 Test 的 issue
    """
    existing = {}

    # 策略1: 子任务
    jql = f'parent = "{parent_key}" ORDER BY created'
    data = jira_get(base_url, f"/search?jql={requests.utils.quote(jql)}&maxResults=200&fields=summary,description,issuetype,customfield_*", auth)
    for issue in data.get("issues", []):
        key = issue["key"]
        fields = issue.get("fields", {})
        existing[key] = {
            "key": key,
            "summary": fields.get("summary", ""),
            "description": fields.get("description", "") or "",
            "issue_type": fields.get("issuetype", {}).get("name", ""),
            "source": "subtask",
        }

    # 策略2: 通过 issue link 关联的测试用例
    jql = (
        f'issue in linkedIssues("{parent_key}") '
        f'AND issuetype in ("Test", "测试用例", "测试") '
        f'ORDER BY created'
    )
    data = jira_get(base_url, f"/search?jql={requests.utils.quote(jql)}&maxResults=200&fields=summary,description", auth)
    for issue in data.get("issues", []):
        key = issue["key"]
        if key not in existing:
            fields = issue.get("fields", {})
            existing[key] = {
                "key": key,
                "summary": fields.get("summary", ""),
                "description": fields.get("description", "") or "",
                "issue_type": fields.get("issuetype", {}).get("name", ""),
                "source": "link",
            }

    return list(existing.values())


# ============================================================
# 文本相似度计算
# ============================================================

def normalize(text: str) -> str:
    """标准化文本用于比较"""
    text = re.sub(r'[^\w一-鿿]', '', text)  # 只保留中文、字母、数字
    return text.lower().strip()


def title_similarity(t1: str, t2: str) -> float:
    """标题相似度 (0~1)"""
    n1, n2 = normalize(t1), normalize(t2)
    if not n1 or not n2:
        return 0.0
    return SequenceMatcher(None, n1, n2).ratio()


def keyword_overlap(t1: str, t2: str) -> float:
    """关键词交集占比 — 捕捉功能关键词相同但措辞不同的情况"""
    # 分词: 按非字母数字中文拆分
    def tokenize(s):
        return set(re.findall(r'[\w一-鿿]+', normalize(s)))
    tok1, tok2 = tokenize(t1), tokenize(t2)
    if not tok1 or not tok2:
        return 0.0
    intersection = tok1 & tok2
    return len(intersection) / max(len(tok1), len(tok2))


def compute_similarity(proposed: dict, existing: dict) -> float:
    """
    综合计算两个用例的相似度。
    考虑: 标题 + 步骤/描述
    """
    p_title = proposed.get("title", "")
    p_steps = " ".join(proposed.get("steps", []))
    p_text = p_title + " " + p_steps
    if proposed.get("expected_results"):
        p_text += " " + " ".join(proposed["expected_results"])

    e_summary = existing.get("summary", "")
    e_desc = existing.get("description", "")

    # 标题相似度权重 0.6
    title_sim = title_similarity(p_title, e_summary)
    kw_sim = keyword_overlap(p_title, e_summary)

    # 内容相似度权重 0.4
    content_sim = title_similarity(p_text, e_summary + " " + e_desc)

    # 综合评分
    score = max(title_sim, kw_sim) * 0.6 + content_sim * 0.4
    return score


# ============================================================
# 去重主逻辑
# ============================================================

# 相似度阈值
SIMILARITY_HIGH = 0.75   # 高度相似 → 自动跳过
SIMILARITY_MEDIUM = 0.50  # 中等相似 → 标记需人工确认


def dedup(proposed: list[dict], existing: list[dict]) -> dict:
    """
    返回去重结果:
      - new: 无重复的新用例
      - skipped: 因高度相似被自动跳过的用例 (附匹配到的已有用例)
      - ambiguous: 中等相似需人工确认的用例
    """
    new_list = []
    skipped_list = []
    ambiguous_list = []

    for tc in proposed:
        best_match = None
        best_score = 0.0

        for et in existing:
            score = compute_similarity(tc, et)
            if score > best_score:
                best_score = score
                best_match = et

        entry = {
            "test_case": tc,
            "best_match": best_match,
            "similarity": round(best_score, 3),
        }

        if best_score >= SIMILARITY_HIGH:
            entry["reason"] = f"与 {best_match['key']} 相似度 {best_score:.0%}，自动跳过"
            skipped_list.append(entry)
        elif best_score >= SIMILARITY_MEDIUM:
            entry["reason"] = f"与 {best_match['key']} 相似度 {best_score:.0%}，需确认是否重复"
            ambiguous_list.append(entry)
        else:
            new_list.append(entry)

    return {
        "new": new_list,
        "skipped": skipped_list,
        "ambiguous": ambiguous_list,
        "summary": {
            "total_proposed": len(proposed),
            "new": len(new_list),
            "skipped": len(skipped_list),
            "ambiguous": len(ambiguous_list),
        },
    }


# ============================================================
# 主入口
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="测试用例去重检查")
    parser.add_argument("--jira-url", required=True, help="Jira 需求的完整 URL")
    parser.add_argument("--input", "-i", required=True, help="新生成的测试用例 JSON 文件")
    parser.add_argument("--output", "-o", default="deduped_test_cases.json", help="去重后输出文件")
    parser.add_argument("--dry-run", action="store_true", help="仅输出去重报告，不生成输出文件")
    args = parser.parse_args()

    # 认证检测
    cookie = os.environ.get("JIRA_COOKIE")
    email = os.environ.get("JIRA_EMAIL")
    api_token = os.environ.get("JIRA_API_TOKEN")
    username = os.environ.get("JIRA_USERNAME")
    password = os.environ.get("JIRA_PASSWORD")
    if not cookie and not (email and api_token) and not (username and password):
        print(
            "请配置认证（优先 Windows 系统环境变量 JIRA_USERNAME/PASSWORD 或 JIRA_USERNAME / JIRA_PASSWORD；可选 config.local.env 兜底）:\n"
            "  复制 config.local.env.example → config.local.env 并填写",
            file=sys.stderr,
        )
        sys.exit(1)

    auth = build_auth_headers()
    base_url, parent_key = parse_jira_url(args.jira_url)

    # 读取新用例
    with open(args.input, "r", encoding="utf-8") as f:
        proposed = json.load(f)

    # 如果输入是 dict 且包含 key "test_cases" 或 "functional"/"api"
    if isinstance(proposed, dict):
        for key in ("test_cases", "functional", "api", "cases"):
            if key in proposed and isinstance(proposed[key], list):
                proposed = proposed[key]
                break

    print(f"\n待检查用例数: {len(proposed)}", file=sys.stderr)

    # 拉取已有用例
    print(f"正在拉取 {parent_key} 下已有测试用例...", file=sys.stderr)
    existing = fetch_existing_test_cases(base_url, parent_key, auth)
    print(f"已有测试用例数: {len(existing)}", file=sys.stderr)

    if existing:
        print("\n已有用例列表:", file=sys.stderr)
        for et in existing:
            print(f"  {et['key']}: {et['summary'][:60]}", file=sys.stderr)

    # 去重
    print("\n去重中...", file=sys.stderr)
    result = dedup(proposed, existing)

    # 报告
    s = result["summary"]
    print(f"\n{'='*50}", file=sys.stderr)
    print(f"去重报告:", file=sys.stderr)
    print(f"  总计: {s['total_proposed']} 个", file=sys.stderr)
    print(f"  新增: {s['new']} 个", file=sys.stderr)
    print(f"  跳过: {s['skipped']} 个 (相似度 ≥ {SIMILARITY_HIGH:.0%})", file=sys.stderr)
    print(f"  存疑: {s['ambiguous']} 个 (相似度 {SIMILARITY_MEDIUM:.0%} ~ {SIMILARITY_HIGH:.0%})", file=sys.stderr)
    print(f"{'='*50}", file=sys.stderr)

    if result["skipped"]:
        print("\n已自动跳过:", file=sys.stderr)
        for item in result["skipped"]:
            tc = item["test_case"]
            print(f"  ✗ [{item['similarity']:.0%}] {tc.get('title', tc.get('case_id', ''))}", file=sys.stderr)
            print(f"    匹配: {item['best_match']['key']} - {item['best_match']['summary'][:50]}", file=sys.stderr)

    if result["ambiguous"]:
        print("\n需人工确认:", file=sys.stderr)
        for item in result["ambiguous"]:
            tc = item["test_case"]
            print(f"  ? [{item['similarity']:.0%}] {tc.get('title', tc.get('case_id', ''))}", file=sys.stderr)
            print(f"    匹配: {item['best_match']['key']} - {item['best_match']['summary'][:50]}", file=sys.stderr)

    if not args.dry_run:
        # 只输出确认新增的用例
        new_cases = [item["test_case"] for item in result["new"]]
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(new_cases, f, ensure_ascii=False, indent=2)
        print(f"\n去重后用例已保存: {args.output}", file=sys.stderr)

    # stdout 输出去重结果 JSON（供下游脚本消费）
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
