#!/usr/bin/env python3
"""
JIRA Issue reader (platform) — fetch issue JSON with Confluence/Figma link extraction.

用法:
  python scripts/get_issue.py --url https://your-domain.atlassian.net/browse/PROJ-123
  python scripts/get_issue.py --url https://your-domain.atlassian.net/browse/PROJ-123 --output data/jira_issue.json
  python scripts/jira_cli.py get-issue --url https://... --output data/jira_issue.json

认证配置（优先本地文件，可不依赖 Multica 环境变量）:
  <skill>/config.local.env  - 推荐；从 config.local.env.example 复制后填写
  或进程环境变量:
  JIRA_EMAIL / JIRA_API_TOKEN / JIRA_COOKIE / JIRA_USERNAME / JIRA_PASSWORD 等

输出:
  - 标准输出或文件: JSON 格式的 Issue 信息(含抽取的 Confluence/Figma 链接)
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
from urllib.parse import urlparse, parse_qs
from html import unescape

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
# 链接匹配模式
# ============================================================

PATTERN_CONFLUENCE = re.compile(
    r'https?://[^/\s]+(?:\.atlassian\.net)[^\]"\'()\s]*(?:wiki/|pages/)[^\s)"\'>]+'
)
PATTERN_FIGMA = re.compile(
    r'https?://[^/\s]+\.figma\.com/(?:file|design|proto)/([a-zA-Z0-9]+)[^\s)""\'>]*'
)


# ============================================================
# Jira API 调用
# ============================================================

def is_self_hosted(url: str) -> bool:
    """检测是否为自部署 Jira（非 atlassian.net）"""
    parsed = urlparse(url)
    return 'atlassian.net' not in parsed.netloc

def get_rest_path() -> str:
    return "/rest/api/2" if ("JIRA_COOKIE" in os.environ or "JIRA_USERNAME" in os.environ or "JIRA_USERNAME" in os.environ) else "/rest/api/3"

def build_auth_headers() -> dict:
    """根据环境变量自动选择认证方式（优先使用用户名密码，防止 cookie 过期）"""
    headers = {"Accept": "application/json"}

    username = os.environ.get("JIRA_USERNAME")
    password = os.environ.get("JIRA_PASSWORD")
    if username and password:
        b = b64encode(f"{username}:{password}".encode()).decode()
        headers["Authorization"] = f"Basic {b}"
        return headers

    # 域账户认证（与 JIRA_USERNAME/JIRA_PASSWORD 同等优先级）
    domain_user = os.environ.get("JIRA_USERNAME")
    domain_pass = os.environ.get("JIRA_PASSWORD")
    if domain_user and domain_pass:
        b = b64encode(f"{domain_user}:{domain_pass}".encode()).decode()
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
        "请配置认证（推荐本地文件，Multica 可不配 Secret）:\n"
        "  1) 复制 config.local.env.example → config.local.env 并填写\n"
        "  2) 或设置环境变量:\n"
        "     自部署: JIRA_USERNAME+PASSWORD 或 JIRA_USERNAME+PASSWORD\n"
        "     Cloud:  JIRA_EMAIL + JIRA_API_TOKEN",
        file=sys.stderr,
    )
    sys.exit(1)


def parse_jira_url(url: str) -> tuple[str, str]:
    """从 Jira URL 解析出 base_url 和 issue_key"""
    parsed = urlparse(url)
    base_url = f"{parsed.scheme}://{parsed.netloc}"
    # URL 形如: https://xx.atlassian.net/browse/PROJ-123 或 http://your-domain.atlassian.net:8080/browse/PROJ-123
    match = re.search(r'/browse/([A-Z]+-\d+)', parsed.path)
    if not match:
        raise ValueError(f"无法从 URL 中解析出 Issue Key: {url}")
    return base_url, match.group(1)


def fetch_issue(base_url: str, issue_key: str, auth_headers: dict) -> dict:
    """获取 Jira Issue 详情（含附件、渲染字段、issuelinks）"""
    rest_path = get_rest_path()
    url = f"{base_url}{rest_path}/issue/{issue_key}"
    resp = requests.get(
        url,
        headers=auth_headers,
        params={
            "expand": "renderedFields",
            "fields": "summary,description,issuetype,status,priority,attachment,issuelinks",
        },
        timeout=30,
    )
    if resp.status_code == 401:
        print("认证失败：请检查 JIRA_USERNAME+JIRA_PASSWORD 或 JIRA_COOKIE 或 JIRA_EMAIL+JIRA_API_TOKEN", file=sys.stderr)
        sys.exit(1)
    if resp.status_code == 404:
        print(f"Issue 不存在: {issue_key}", file=sys.stderr)
        sys.exit(1)
    resp.raise_for_status()
    return resp.json()


# ============================================================
# 文本提取
# ============================================================

def extract_text_from_adf(adf: dict | str | None) -> str:
    """递归提取 Atlassian Document Format 中的纯文本"""
    if adf is None:
        return ""
    if isinstance(adf, str):
        return adf
    texts = []
    if isinstance(adf, dict):
        if adf.get("type") == "text" and "text" in adf:
            texts.append(adf["text"])
        for key in ("content", "items", "args"):
            child = adf.get(key)
            if isinstance(child, list):
                for item in child:
                    texts.append(extract_text_from_adf(item))
            elif isinstance(child, dict):
                texts.append(extract_text_from_adf(child))
    return " ".join(texts)


def extract_text_with_structure(adf: dict | str | None) -> str:
    """从 ADF 中提取结构化 Markdown 文本（保留表格、列表、格式化等结构）

    与 extract_text_from_adf 不同：此函数保留 ADF 中的结构信息（表格行列、列表层级、
    格式化标记），输出为 Markdown 格式，而非纯文本拼接。
    """
    if adf is None:
        return ""
    if isinstance(adf, str):
        return adf

    result_parts = []

    def process_node(node: dict, indent: str = "") -> str:
        """递归处理 ADF 节点，返回 Markdown 文本"""
        if not isinstance(node, dict):
            return str(node) if node is not None else ""

        node_type = node.get("type", "")
        content = node.get("content") or []
        text_val = node.get("text", "")
        marks = node.get("marks") or []
        attrs = node.get("attrs") or {}

        # 文本节点
        if node_type == "text" and text_val:
            formatted = text_val
            for mark in marks:
                mark_type = mark.get("type", "")
                if mark_type == "strong":
                    formatted = f"**{formatted}**"
                elif mark_type == "em":
                    formatted = f"*{formatted}*"
                elif mark_type == "code":
                    formatted = f"`{formatted}`"
                elif mark_type == "strike":
                    formatted = f"~~{formatted}~~"
                elif mark_type == "underline":
                    formatted = f"<u>{formatted}</u>"
                elif mark_type == "link":
                    href = mark.get("attrs", {}).get("href", "")
                    formatted = f"[{formatted}]({href})"
                elif mark_type == "subsup":
                    type_ = mark.get("attrs", {}).get("type", "")
                    formatted = f"^{formatted}^" if type_ == "sup" else f"~{formatted}~"
            return formatted

        # 段落
        if node_type == "paragraph":
            inner = "".join(process_node(c) for c in content)
            return f"\n\n{inner}\n\n" if inner.strip() else ""

        # 标题
        if node_type.startswith("heading"):
            level = attrs.get("level", 1)
            inner = "".join(process_node(c) for c in content)
            return f"\n\n{'#' * level} {inner}\n\n"

        # 列表
        if node_type == "bulletList":
            items = []
            for c in content:
                item_text = process_node(c, indent + "  ")
                items.append(f"{indent}- {item_text.strip()}")
            return "\n" + "\n".join(items) + "\n"

        if node_type == "orderedList":
            order = attrs.get("order", 1)
            items = []
            for i, c in enumerate(content):
                item_text = process_node(c, indent + "   ")
                items.append(f"{indent}{order + i}. {item_text.strip()}")
            return "\n" + "\n".join(items) + "\n"

        if node_type == "listItem":
            inner = "".join(process_node(c, indent) for c in content)
            return inner

        # 表格
        if node_type == "table":
            rows = []
            for c in content:
                row_text = process_node(c)
                if row_text:
                    rows.append(row_text)

            if not rows:
                return "\n\n[空表格]\n\n"

            # 第一行作为表头
            header_cells = rows[0].split("|")
            col_count = len(header_cells) - 2 if len(header_cells) > 2 else 3

            md = "\n\n" + rows[0] + "\n"
            md += "| " + " | ".join(["---"] * col_count) + " |\n"
            md += "\n".join(rows[1:]) + "\n\n"
            return md

        if node_type == "tableRow":
            cells = []
            for c in content:
                cell_text = process_node(c)
                cells.append(cell_text)
            return "| " + " | ".join(cells) + " |"

        if node_type == "tableHeader" or node_type == "tableCell":
            inner = "".join(process_node(c) for c in content)
            return inner.strip()

        # 代码块
        if node_type == "codeBlock":
            lang = attrs.get("language", "")
            inner = "".join(process_node(c) for c in content)
            return f"\n```{lang}\n{inner}\n```\n"

        # 引用块
        if node_type == "blockquote":
            inner = "".join(process_node(c) for c in content)
            lines = inner.strip().split("\n")
            quoted = "\n".join(f"> {line}" for line in lines)
            return f"\n\n{quoted}\n\n"

        # 分隔线
        if node_type == "rule":
            return "\n\n---\n\n"

        # 硬换行
        if node_type == "hardBreak":
            return "\n"

        # 内联卡片（通常用于链接预览）
        if node_type == "inlineCard":
            url = attrs.get("url", "")
            return f" [{url}] " if url else " [链接] "

        # 媒体/图片
        if node_type == "media":
            url = attrs.get("url", "")
            id_ = attrs.get("id", "")
            collection = attrs.get("collection", "")
            alt = ""
            for m in marks:
                if m.get("type") == "link":
                    alt_parts = []
                    for link_c in m.get("attrs", {}).get("href", ""):
                        alt_parts.append(str(link_c))
            return f"\n![图片: {id_}](id:{id_})\n" if id_ else ""

        if node_type == "mediaGroup":
            inner = "".join(process_node(c) for c in content)
            return f"\n[媒体组]\n{inner}\n[/媒体组]\n"

        if node_type == "mediaSingle":
            inner = "".join(process_node(c) for c in content)
            return f"\n{inner}\n"

        # 任务列表
        if node_type == "taskList":
            inner = "".join(process_node(c, indent) for c in content)
            return f"\n{inner}\n"

        if node_type == "taskItem":
            state = attrs.get("state", "TODO")
            check = "[x]" if state == "DONE" else "[ ]"
            inner = "".join(process_node(c, indent) for c in content)
            return f"{indent}- {check} {inner.strip()}\n"

        # 决策列表
        if node_type == "decisionList":
            inner = "".join(process_node(c, indent) for c in content)
            return f"\n{inner}\n"

        if node_type == "decisionItem":
            inner = "".join(process_node(c, indent) for c in content)
            return f"{indent}- 💡 {inner.strip()}\n"

        # 面板/容器（类似 Confluence 的 info panel）
        if node_type == "panel":
            panel_type = attrs.get("panelType", "info")
            inner = "".join(process_node(c) for c in content)
            return f"\n> **[{panel_type.upper()}]** {inner}\n"

        # 展开/折叠
        if node_type == "expand":
            title = attrs.get("title", "展开")
            inner = "".join(process_node(c) for c in content)
            return f"\n<details><summary>{title}</summary>\n{inner}\n</details>\n"

        # 嵌套内容（递归处理 content）
        inner = "".join(process_node(c, indent) for c in content)
        return inner

    for node in content if isinstance(content, list) else []:
        part = process_node(node)
        if part:
            result_parts.append(part)

    text = "".join(result_parts)
    # 清理多余空行
    text = re.sub(r'\n{4,}', '\n\n\n', text)
    return text.strip()


def extract_links_from_text(text: str) -> dict:
    """从文本中提取 Confluence 和 Figma 链接"""
    # Jira description 中可能包含 HTML 编码
    text = unescape(text)
    confluence_links = list(set(PATTERN_CONFLUENCE.findall(text)))
    figma_links = list(set(PATTERN_FIGMA.findall(text)))
    # 去重并整理完整链接
    figma_full = []
    for fl in figma_links:
        # fl 可能是 file key，也可能是部分 URL，重新构建
        full_links = PATTERN_FIGMA.findall(text)
        # 用原始匹配来获取完整链接
        figma_full = list(set(PATTERN_FIGMA.findall(text)))

    # 重新匹配完整 Figma URL
    figma_urls = list(set(re.findall(
        r'https?://[^/\s]+\.figma\.com/(?:file|design|proto)/[a-zA-Z0-9]+[^\s)""\'>]*',
        text
    )))

    return {
        "confluence_links": confluence_links,
        "figma_links": figma_urls,
    }


def get_custom_field_value(field_value) -> str:
    """从自定义字段的各种可能格式中提取字符串"""
    if isinstance(field_value, dict):
        return field_value.get("value", field_value.get("name", ""))
    if isinstance(field_value, list):
        return ", ".join(get_custom_field_value(v) for v in field_value)
    if isinstance(field_value, str):
        return field_value
    return str(field_value) if field_value else ""


# ============================================================
# 关联 Issue
# ============================================================

def extract_linked_issues(fields: dict) -> list:
    """从 issuelinks 字段提取关联 Issue 摘要"""
    linked = []
    for link in fields.get("issuelinks") or []:
        link_type = link.get("type") or {}
        type_name = link_type.get("name", "")
        if link.get("inwardIssue"):
            direction = "inward"
            issue_ref = link["inwardIssue"]
            rel = link_type.get("inward", "")
        elif link.get("outwardIssue"):
            direction = "outward"
            issue_ref = link["outwardIssue"]
            rel = link_type.get("outward", "")
        else:
            continue
        issue_fields = issue_ref.get("fields") or {}
        status_obj = issue_fields.get("status") or {}
        linked.append({
            "key": issue_ref.get("key", ""),
            "summary": issue_fields.get("summary", ""),
            "status": status_obj.get("name", ""),
            "link_type": type_name,
            "relation": rel,
            "direction": direction,
        })
    return linked


def fetch_linked_issue_details(
    base_url: str, auth_headers: dict, linked_keys: list[str]
) -> list:
    """对每个关联 KEY 再拉一层描述与链接（仅一层，避免爆炸式请求）"""
    details = []
    seen = set()
    for key in linked_keys:
        if not key or key in seen:
            continue
        seen.add(key)
        try:
            issue_data = fetch_issue(base_url, key, auth_headers)
            brief = process_issue(issue_data, fetch_linked=False)
            details.append({
                "key": brief["key"],
                "summary": brief["summary"],
                "status": brief["status"],
                "description_text": brief["description_text"],
                "links": brief["links"],
            })
        except Exception as exc:
            details.append({"key": key, "error": str(exc)})
    return details


# ============================================================
# 主流程
# ============================================================

def process_issue(issue_data: dict, fetch_linked: bool = False, base_url: str = "", auth_headers: dict | None = None) -> dict:
    """处理 Issue 数据，提取关键信息"""
    fields = issue_data.get("fields", {})

    # 基础信息
    summary = fields.get("summary", "")
    desc = fields.get("description")

    # 获取 HTML 渲染的描述（来自 renderedFields）
    rendered_fields = issue_data.get("renderedFields", {})
    rendered_desc = rendered_fields.get("description", "")

    # 处理 description 可能是 ADF 或纯字符串
    if isinstance(desc, str):
        description_text = desc
        description_html = desc
        adf_content = None
    else:
        description_text = extract_text_from_adf(desc)
        description_html = extract_text_with_structure(desc)  # 结构化 Markdown
        adf_content = desc  # 保留原始 ADF 结构

    # 如果 renderedFields 中有 HTML 描述，说明 Jira 自带了 HTML 渲染版本
    # 这比我们的 ADF 解析更准确（特别对于表格、嵌入内容等）
    if rendered_desc:
        description_html = f"{description_html}\n\n---\n\n### Jira Rendered HTML:\n\n{rendered_desc}"

    # 类型、状态、优先级
    issue_type = fields.get("issuetype", {}).get("name", "")
    status = fields.get("status", {}).get("name", "")
    priority = fields.get("priority", {}).get("name", "")

    # 提取链接
    all_text = f"{summary}\n{description_text}"
    links = extract_links_from_text(all_text)

    # 提取附件中的图片
    attachments = fields.get("attachment", [])
    image_attachments = []
    for att in attachments:
        mime = att.get("mimeType", "")
        if mime.startswith("image/"):
            image_attachments.append({
                "id": att.get("id", ""),
                "filename": att.get("filename", ""),
                "mimeType": mime,
                "size": att.get("size", 0),
                "content_url": att.get("content", ""),  # 下载 URL
                "thumbnail_url": att.get("thumbnail", ""),  # 缩略图 URL
            })

    linked_issues = extract_linked_issues(fields)

    # 构建结果
    result = {
        "key": issue_data.get("key", ""),
        "summary": summary,
        "issue_type": issue_type,
        "status": status,
        "priority": priority,
        "description_text": description_text,
        "description_html": description_html,  # 结构化 Markdown 文本
        "adf_content": adf_content,  # 原始 ADF 内容（若为 ADF 格式）
        "image_attachments": image_attachments,  # 图片附件列表
        "links": links,
        "linked_issues": linked_issues,
        "self_url": issue_data.get("self", ""),
    }

    if fetch_linked and base_url and auth_headers and linked_issues:
        keys = [item["key"] for item in linked_issues if item.get("key")]
        result["linked_issues_detail"] = fetch_linked_issue_details(
            base_url, auth_headers, keys
        )

    return result


def main():
    parser = argparse.ArgumentParser(description="从 Jira Issue 提取需求信息")
    parser.add_argument("--url", required=True, help="Jira Issue 的完整 URL")
    parser.add_argument("--output", "-o", help="输出文件路径（默认输出到 stdout）")
    parser.add_argument(
        "--with-linked",
        action="store_true",
        help="额外拉取 linked_issues 中各 Issue 的描述与 Confluence/Figma 链接（一层）",
    )
    args = parser.parse_args()

    # 认证信息 — 支持 Cookie / Basic Auth (用户名密码) / Cloud API Token
    cookie = os.environ.get("JIRA_COOKIE")
    email = os.environ.get("JIRA_EMAIL")
    api_token = os.environ.get("JIRA_API_TOKEN")
    username = os.environ.get("JIRA_USERNAME")
    password = os.environ.get("JIRA_PASSWORD")
    domain_user = os.environ.get("JIRA_USERNAME")
    domain_pass = os.environ.get("JIRA_PASSWORD")
    if not (username and password) and not (domain_user and domain_pass) and not (email and api_token) and not cookie:
        print(
            "请配置认证（优先 Windows 系统环境变量 JIRA_USERNAME/PASSWORD 或 JIRA_USERNAME / JIRA_PASSWORD；可选 config.local.env 兜底）:\n"
            "  复制 config.local.env.example → config.local.env 并填写",
            file=sys.stderr,
        )
        sys.exit(1)

    # 解析 URL 并获取 Issue
    base_url, issue_key = parse_jira_url(args.url)
    auth_headers = build_auth_headers()
    issue_data = fetch_issue(base_url, issue_key, auth_headers)
    result = process_issue(
        issue_data,
        fetch_linked=args.with_linked,
        base_url=base_url,
        auth_headers=auth_headers,
    )

    # 输出
    output = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output)
        print(f"结果已写入: {args.output}", file=sys.stderr)
    else:
        print(output)


if __name__ == "__main__":
    main()
