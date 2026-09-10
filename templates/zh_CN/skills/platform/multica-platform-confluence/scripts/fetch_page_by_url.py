#!/usr/bin/env python3
"""
Confluence page reader by URL (platform) — Markdown + rich JSON + optional image download.

用法:
  python scripts/fetch_page_by_url.py --url https://your-domain.atlassian.net/wiki/spaces/SPACE/pages/123456
  python scripts/fetch_page_by_url.py --url http://your-domain.atlassian.net/wiki:8090/pages/viewpage.action?pageId=123

环境变量:
  JIRA_EMAIL         - Atlassian Cloud 账号邮箱（配合 JIRA_API_TOKEN 使用）
  JIRA_API_TOKEN     - Atlassian Cloud API Token
  CONFLUENCE_COOKIE  - 自部署 Confluence 的 Cookie（如 "JSESSIONID=xxx"）
  注意: 自部署 Confluence 与 Jira Cookie 通常不同，需要分别设置

输出:
  - Markdown 格式的需求文档内容（纯文本/文件）
  - JSON 格式的页面结构信息（含标题、层级、表格、html_content、image_references 等）
  - 默认下载页面图片附件到 --image-dir（可用 --no-images 跳过）
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
from html import unescape
from pathlib import Path
from urllib.parse import urlparse, parse_qs, unquote

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
# Confluence API
# ============================================================

def build_auth_headers() -> dict:
    """根据环境变量自动选择认证方式（优先使用用户名密码）"""
    headers = {"Accept": "application/json"}

    username = os.environ.get("JIRA_USERNAME")
    password = os.environ.get("JIRA_PASSWORD")
    if username and password:
        b = b64encode(f"{username}:{password}".encode()).decode()
        headers["Authorization"] = f"Basic {b}"
        return headers

    # 域账户认证（与 JIRA_USERNAME/PASSWORD 同等优先级）
    domain_user = os.environ.get("JIRA_USERNAME")
    domain_pass = os.environ.get("JIRA_PASSWORD")
    if domain_user and domain_pass:
        b = b64encode(f"{domain_user}:{domain_pass}".encode()).decode()
        headers["Authorization"] = f"Basic {b}"
        return headers

    email = os.environ.get("JIRA_EMAIL")
    api_token = os.environ.get("JIRA_API_TOKEN")
    if email and api_token:
        token = b64encode(f"{email}:{api_token}".encode()).decode()
        headers["Authorization"] = f"Basic {token}"
        return headers

    cookie = os.environ.get("CONFLUENCE_COOKIE")
    if cookie:
        headers["Cookie"] = cookie
        return headers

    print(
        "请配置认证（优先 Windows 系统环境变量 JIRA_USERNAME/PASSWORD 或 JIRA_USERNAME / JIRA_PASSWORD；可选 config.local.env 兜底）:\n"
        "  自部署: JIRA_USERNAME+PASSWORD 或 JIRA_USERNAME+PASSWORD\n"
        "  或 CONFLUENCE_COOKIE；Cloud: JIRA_EMAIL + JIRA_API_TOKEN",
        file=sys.stderr,
    )
    sys.exit(1)


def parse_confluence_url(url: str) -> tuple[str, int | None, str | None]:
    """
    从 Confluence URL 解析 base_url, page_id, space_key。
    URL 格式:
      - Cloud: https://xx.atlassian.net/wiki/spaces/SPACE/pages/123456?...
      - 自部署: http://your-domain.atlassian.net/wiki:8090/pages/viewpage.action?pageId=123456
      - https://xx.atlassian.net/wiki/spaces/SPACE/overview
    """
    parsed = urlparse(url)
    base_url = f"{parsed.scheme}://{parsed.netloc}"

    page_id = None
    space_key = None

    # 尝试匹配 /pages/PAGE_ID 模式（Cloud + Server 通用）
    m = re.search(r'/pages/(\d+)', parsed.path)
    if m:
        page_id = int(m.group(1))

    # 尝试从 query string 取 pageId（自部署 viewpage.action 格式）
    if not page_id:
        params = parse_qs(parsed.query)
        if "pageId" in params:
            page_id = int(params["pageId"][0])

    # 尝试匹配 /spaces/KEY 模式
    m = re.search(r'/spaces/([A-Z0-9_]+)', parsed.path)
    if m:
        space_key = m.group(1)

    return base_url, page_id, space_key


def fetch_page_by_id(base_url: str, page_id: int, auth_headers: dict) -> dict:
    """通过页面 ID 获取 Confluence 页面内容"""
    # 自部署 Confluence 使用 /rest/api/content/{id}，Cloud 使用 /wiki/api/v2/pages/{id}
    # 先尝试 Cloud 的 v2 API，如果 404 则降级到 Server 的 API
    urls_to_try = [
        f"{base_url}/wiki/api/v2/pages/{page_id}",
        f"{base_url}/rest/api/content/{page_id}",
    ]

    last_error = None
    for url in urls_to_try:
        try:
            resp = requests.get(
                url,
                headers=auth_headers,
                params={"expand": "body.storage,version,space"} if "rest/api" in url else {"body-format": "storage"},
                timeout=30,
            )
            if resp.status_code == 200:
                return resp.json()
            last_error = (resp.status_code, resp.text[:200])
        except requests.RequestException as e:
            last_error = (0, str(e))

    # 都失败了
    if last_error and last_error[0] == 401:
        print("认证失败：请检查 CONFLUENCE_COOKIE 或 JIRA_EMAIL+JIRA_API_TOKEN", file=sys.stderr)
    elif last_error:
        print(f"Confluence 页面不存在或无法访问: pageId={page_id} (last error: {last_error[0]})", file=sys.stderr)
    sys.exit(1)


def fetch_page_children(base_url: str, page_id: int, auth_headers: dict) -> list[dict]:
    """获取页面的子页面列表"""
    url = f"{base_url}/wiki/api/v2/pages/{page_id}/children"
    resp = requests.get(
        url,
        headers={**auth_headers, "Accept": "application/json"},
        params={"limit": 100},
        timeout=30,
    )
    if resp.status_code == 200:
        data = resp.json()
        return data.get("results", [])
    return []


def fetch_page_attachments(base_url: str, page_id: int, auth_headers: dict) -> list[dict]:
    """获取页面附件列表（含图片）。"""
    url = f"{base_url}/rest/api/content/{page_id}/child/attachment"
    try:
        resp = requests.get(
            url,
            headers=auth_headers,
            params={"limit": 200, "expand": "version"},
            timeout=60,
        )
        if resp.status_code != 200:
            return []
        results = resp.json().get("results", [])
        attachments = []
        for item in results:
            links = item.get("_links") or {}
            download = links.get("download") or links.get("downloadUrl") or ""
            if download and download.startswith("/"):
                download = base_url.rstrip("/") + download
            attachments.append(
                {
                    "id": item.get("id"),
                    "title": item.get("title") or "",
                    "media_type": (item.get("metadata") or {}).get("mediaType")
                    or item.get("extensions", {}).get("mediaType")
                    or "",
                    "download_url": download,
                }
            )
        return attachments
    except requests.RequestException as e:
        print(f"获取附件列表失败: {e}", file=sys.stderr)
        return []


def extract_image_references(html_content: str) -> list[dict]:
    """从 Storage HTML 提取图片引用（附件名 / 外链）。"""
    refs = []
    seen = set()
    for m in re.finditer(
        r'<ri:attachment[^>]*ri:filename="([^"]+)"[^>]*/?>',
        html_content or "",
        flags=re.IGNORECASE,
    ):
        name = unescape(m.group(1)).strip()
        key = ("attachment", name)
        if name and key not in seen:
            seen.add(key)
            refs.append({"type": "attachment", "filename": name})
    for m in re.finditer(r'<img[^>]*src="([^"]+)"[^>]*>', html_content or "", flags=re.IGNORECASE):
        url = unescape(m.group(1)).strip()
        key = ("url", url)
        if url and key not in seen:
            seen.add(key)
            refs.append({"type": "url", "url": url})
    return refs


def download_images(
    base_url: str,
    page_id: int,
    auth_headers: dict,
    image_refs: list[dict],
    image_dir: str,
) -> list[dict]:
    """下载页面图片附件/外链到本地目录，返回下载结果列表。"""
    os.makedirs(image_dir, exist_ok=True)
    attachments = fetch_page_attachments(base_url, page_id, auth_headers)
    by_name = {a["title"]: a for a in attachments if a.get("title")}
    downloaded = []

    # 若 HTML 未显式引用，也把附件中的图片一并下载
    names_from_refs = {r["filename"] for r in image_refs if r.get("type") == "attachment" and r.get("filename")}
    for att in attachments:
        title = att.get("title") or ""
        media = (att.get("media_type") or "").lower()
        if title and (title in names_from_refs or media.startswith("image/") or title.lower().endswith(
            (".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp")
        )):
            if title not in names_from_refs:
                image_refs.append({"type": "attachment", "filename": title})

    session_headers = dict(auth_headers)
    for idx, ref in enumerate(image_refs, 1):
        try:
            if ref.get("type") == "attachment":
                att = by_name.get(ref.get("filename") or "")
                if not att or not att.get("download_url"):
                    downloaded.append({**ref, "status": "missing", "path": None})
                    continue
                url = att["download_url"]
                filename = att["title"] or f"attachment_{idx}"
            else:
                url = ref.get("url") or ""
                if not url:
                    continue
                if url.startswith("/"):
                    url = base_url.rstrip("/") + url
                filename = unquote(Path(urlparse(url).path).name) or f"image_{idx}.png"

            safe_name = re.sub(r'[<>:"/\\|?*]', "_", filename)
            out_path = os.path.join(image_dir, safe_name)
            resp = requests.get(url, headers=session_headers, timeout=60)
            if resp.status_code != 200:
                downloaded.append({**ref, "status": f"http_{resp.status_code}", "path": None})
                continue
            with open(out_path, "wb") as f:
                f.write(resp.content)
            downloaded.append(
                {
                    **ref,
                    "status": "ok",
                    "path": out_path,
                    "bytes": len(resp.content),
                }
            )
            print(f"  ✓ 图片已下载: {out_path}", file=sys.stderr)
        except Exception as e:
            downloaded.append({**ref, "status": f"error:{e}", "path": None})
            print(f"  ✗ 图片下载失败: {ref}: {e}", file=sys.stderr)
    return downloaded


def _expand_structured_macros(html: str) -> str:
    """保留宏内文本，避免整段删除导致需求信息丢失。"""

    def _repl(match: re.Match) -> str:
        block = match.group(0)
        bodies = re.findall(
            r"<ac:(?:plain-text-body|rich-text-body)[^>]*>\s*(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?\s*</ac:(?:plain-text-body|rich-text-body)>",
            block,
            flags=re.DOTALL | re.IGNORECASE,
        )
        if not bodies:
            return "\n"
        text = "\n\n".join(b.strip() for b in bodies if b and b.strip())
        return f"\n\n{text}\n\n" if text else "\n"

    return re.sub(
        r"<ac:structured-macro[^>]*>.*?</ac:structured-macro>",
        _repl,
        html,
        flags=re.DOTALL | re.IGNORECASE,
    )


# ============================================================
# HTML/Storage 格式 → Markdown 转换
# ============================================================

def storage_to_markdown(html_content: str) -> str:
    """将 Confluence Storage Format (HTML) 转换为 Markdown"""
    text = html_content

    # 展开宏内容（保留正文），不再直接删除整个宏
    text = _expand_structured_macros(text)

    # 处理表格
    text = re.sub(r'<table[^>]*>', '\n\n| ', text)
    text = text.replace('</tr>', ' |\n')
    text = re.sub(r'<t[hd][^>]*>', '| ', text)
    text = text.replace('</t[hd]>', ' ')
    text = re.sub(r'</?tbody[^>]*>', '', text)
    text = text.replace('</table>', '\n')

    # 替换标题
    for i in range(6, 0, -1):
        text = re.sub(rf'<h{i}[^>]*>(.*?)</h{i}>', lambda m: '#' * i + ' ' + m.group(1), text)

    # 列表
    text = re.sub(r'<li[^>]*>(.*?)</li>', lambda m: '- ' + m.group(1), text)
    text = re.sub(r'</?ul[^>]*>', '\n', text)
    text = re.sub(r'</?ol[^>]*>', '\n', text)

    # 段落
    text = re.sub(r'<p[^>]*>(.*?)</p>', lambda m: '\n\n' + m.group(1) + '\n\n', text)

    # 加粗/斜体
    text = re.sub(r'<strong>(.*?)</strong>', r'**\1**', text)
    text = re.sub(r'<em>(.*?)</em>', r'*\1*', text)

    # 链接
    text = re.sub(r'<a[^>]*href="([^"]*)"[^>]*>(.*?)</a>', r'[\2](\1)', text)

    # 图片
    text = re.sub(r'<img[^>]*src="([^"]*)"[^>]*>', r'![](\1)', text)

    # 代码块
    text = re.sub(r'<pre[^>]*>(.*?)</pre>', lambda m: '\n```\n' + m.group(1) + '\n```\n', text)
    text = re.sub(r'<code[^>]*>(.*?)</code>', r'`\1`', text)

    # 水平线
    text = re.sub(r'<hr[^>]*>', '\n---\n', text)

    # 换行
    text = text.replace('<br/>', '\n').replace('<br>', '\n')

    # 移除剩余标签
    text = re.sub(r'<[^>]+>', '', text)

    # 解码 HTML 实体
    text = unescape(text)

    # 清理多余空行
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = text.strip()

    # 清理 Confluence wiki 标记（如 {LQ}{RQ}），确保输出可读
    text = clean_confluence_markers(text)

    return text


def clean_confluence_markers(text: str) -> str:
    """清理 Confluence wiki 标记符"""
    text = re.sub(r'\{LQ\}', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\{RQ\}', '', text, flags=re.IGNORECASE)
    return text


def extract_tables_from_html(html_content: str) -> list[list[list[str]]]:
    """从 Confluence 的 Table 中提取结构化数据"""
    tables = []
    # 简易表格提取（对于复杂格式，只提取纯文本内容）
    table_matches = re.finditer(
        r'<table[^>]*>(.*?)</table>', html_content, re.DOTALL
    )
    for tm in table_matches:
        table_html = tm.group(1)
        rows = re.findall(r'<tr[^>]*>(.*?)</tr>', table_html, re.DOTALL)
        table_data = []
        for row in rows:
            cells = re.findall(r'<t[hd][^>]*>(.*?)</t[hd]>', row, re.DOTALL)
            cell_texts = [re.sub(r'<[^>]+>', '', unescape(c)).strip() for c in cells]
            table_data.append(cell_texts)
        if table_data:
            tables.append(table_data)
    return tables


# ============================================================
# 主流程
# ============================================================

def process_page(page_data: dict) -> dict:
    """处理 Confluence 页面数据"""
    title = page_data.get("title", "")

    # 尝试获取 body.storage.value (v2 API)
    body = page_data.get("body", {})
    storage = body.get("storage", {})
    html_content = storage.get("value", "")

    # 提取版本信息
    version = page_data.get("version", {}).get("number", 1)
    created_at = page_data.get("createdAt", "")
    updated_at = page_data.get("version", {}).get("createdAt", page_data.get("updatedAt", ""))

    # 转换为 Markdown
    markdown = storage_to_markdown(html_content)
    tables = extract_tables_from_html(html_content)
    image_refs = extract_image_references(html_content)
    has_tables = bool(tables)
    has_lists = bool(re.search(r"<(?:ul|ol|li)\b", html_content or "", flags=re.IGNORECASE))
    has_images = bool(image_refs) or bool(
        re.search(r"<ac:image\b|<img\b", html_content or "", flags=re.IGNORECASE)
    )

    result = {
        "title": title,
        "version": version,
        "created_at": created_at,
        "updated_at": updated_at,
        "markdown_content": markdown,
        "html_content": html_content,
        "tables": tables,
        "image_references": image_refs,
        "downloaded_images": [],
        "has_content": bool(markdown.strip()),
        "has_rich_content": {
            "has_tables": has_tables,
            "has_lists": has_lists,
            "has_images": has_images,
        },
    }
    return result


def main():
    parser = argparse.ArgumentParser(description="从 Confluence 拉取需求文档")
    parser.add_argument("--url", required=True, help="Confluence 页面的完整 URL")
    parser.add_argument("--output", "-o", help="输出 Markdown 文件路径")
    parser.add_argument("--json", "-j", help="输出结构化 JSON 文件路径（含表格数据）")
    parser.add_argument(
        "--image-dir",
        default=None,
        help="图片下载目录；默认在 --json 同级创建 confluence_images_<pageId>",
    )
    parser.add_argument("--no-images", action="store_true", help="跳过图片附件下载")
    parser.add_argument("--include-children", action="store_true", help="是否包含子页面内容")
    args = parser.parse_args()

    # 检测认证方式
    cookie = os.environ.get("CONFLUENCE_COOKIE")
    email = os.environ.get("JIRA_EMAIL")
    api_token = os.environ.get("JIRA_API_TOKEN")
    username = os.environ.get("JIRA_USERNAME")
    password = os.environ.get("JIRA_PASSWORD")
    domain_user = os.environ.get("JIRA_USERNAME")
    domain_pass = os.environ.get("JIRA_PASSWORD")
    if not cookie and not (email and api_token) and not (username and password) \
            and not (domain_user and domain_pass):
        print(
            "请配置认证（优先 Windows 系统环境变量 JIRA_USERNAME/PASSWORD 或 JIRA_USERNAME / JIRA_PASSWORD；可选 config.local.env 兜底）:\n"
            "  复制 config.local.env.example → config.local.env 并填写",
            file=sys.stderr,
        )
        sys.exit(1)

    base_url, page_id, space_key = parse_confluence_url(args.url)
    if not page_id:
        print(f"无法从 URL 中解析出页面 ID: {args.url}", file=sys.stderr)
        sys.exit(1)

    auth_headers = build_auth_headers()

    # 获取主页面
    page_data = fetch_page_by_id(base_url, page_id, auth_headers)
    result = process_page(page_data)
    result["page_id"] = page_id

    # 图片下载（默认开启；可用 --no-images 关闭）
    image_dir = args.image_dir
    if not args.no_images:
        if not image_dir:
            base_dir = "."
            if args.json:
                base_dir = os.path.dirname(os.path.abspath(args.json)) or "."
            elif args.output:
                base_dir = os.path.dirname(os.path.abspath(args.output)) or "."
            image_dir = os.path.join(base_dir, f"confluence_images_{page_id}")
        result["downloaded_images"] = download_images(
            base_url,
            page_id,
            auth_headers,
            list(result.get("image_references") or []),
            image_dir,
        )
        result["image_dir"] = image_dir

    # 子页面
    if args.include_children:
        children = fetch_page_children(base_url, page_id, auth_headers)
        child_results = []
        for child in children:
            child_id = child.get("id")
            if child_id:
                try:
                    child_data = fetch_page_by_id(base_url, int(child_id), auth_headers)
                    child_result = process_page(child_data)
                    child_result["page_id"] = int(child_id)
                    if not args.no_images and image_dir:
                        child_img_dir = os.path.join(image_dir, f"child_{child_id}")
                        child_result["downloaded_images"] = download_images(
                            base_url,
                            int(child_id),
                            auth_headers,
                            list(child_result.get("image_references") or []),
                            child_img_dir,
                        )
                        child_result["image_dir"] = child_img_dir
                    child_results.append(child_result)
                except Exception as e:
                    print(f"获取子页面 {child_id} 失败: {e}", file=sys.stderr)
        result["child_pages"] = child_results

    # 输出
    if args.output:
        os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
        content = f"# {result['title']}\n\n> 版本: {result['version']} | 更新于: {result['updated_at']}\n\n{result['markdown_content']}"
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Markdown 已写入: {args.output}", file=sys.stderr)

    if args.json:
        os.makedirs(os.path.dirname(args.json) or ".", exist_ok=True)
        with open(args.json, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"JSON 已写入: {args.json}", file=sys.stderr)

    if not args.output and not args.json:
        # 只打印 Markdown
        print(f"\n# {result['title']}\n")
        print(result["markdown_content"])


if __name__ == "__main__":
    main()
