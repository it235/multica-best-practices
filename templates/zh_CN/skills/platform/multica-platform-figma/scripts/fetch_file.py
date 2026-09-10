#!/usr/bin/env python3
"""
Figma file reader (platform) — structured design metadata + text summary.

用法:
  python scripts/fetch_file.py --url https://www.figma.com/file/ABC123/design?node-id=0-1
  python scripts/fetch_file.py --url https://www.figma.com/design/ABC123/design --output data/figma_design.json

环境变量:
  FIGMA_TOKEN  - Figma Personal Access Token（从 Figma > Settings > Account > Personal Access Tokens 获取）

输出:
  - JSON 格式的设计信息（包含页面、画板、组件、图层、样式等元数据）
  - 文本摘要（可供 Claude 直接阅读）
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
# Figma API
# ============================================================

FIGMA_API_BASE = "https://api.figma.com/v1"


def build_headers() -> dict:
    token = os.environ.get("FIGMA_TOKEN", "")
    if not token:
        print(
            "请配置 FIGMA_TOKEN（推荐写入 skill 目录 config.local.env）\n"
            "  从 Figma > Settings > Account > Personal Access Tokens 生成",
            file=sys.stderr,
        )
        sys.exit(1)
    return {"X-Figma-Token": token}


def parse_figma_url(url: str) -> tuple[str, str | None]:
    """
    从 Figma URL 解析 file_key 和 node_id。
    URL 格式:
      - https://www.figma.com/file/ABC123/design-name
      - https://www.figma.com/file/ABC123/design-name?node-id=0-1
      - https://www.figma.com/design/ABC123/design-name
      - https://www.figma.com/proto/ABC123/design-name
    """
    parsed = urlparse(url)

    # 提取 file_key: /file/KEY 或 /design/KEY 或 /proto/KEY
    m = re.search(r'/(?:file|design|proto)/([a-zA-Z0-9]+)', parsed.path)
    if not m:
        raise ValueError(f"无法从 URL 中解析出 File Key: {url}")
    file_key = m.group(1)

    # 提取 node-id
    params = parse_qs(parsed.query)
    node_id = params.get("node-id", [None])[0]

    return file_key, node_id


def fetch_file_info(file_key: str, headers: dict) -> dict:
    """获取 Figma 文件元数据"""
    url = f"{FIGMA_API_BASE}/files/{file_key}"
    resp = requests.get(url, headers=headers, timeout=60)
    if resp.status_code == 403:
        print("认证失败：请检查 FIGMA_TOKEN 是否有权限访问该文件", file=sys.stderr)
        sys.exit(1)
    if resp.status_code == 404:
        print(f"Figma 文件不存在: {file_key}", file=sys.stderr)
        sys.exit(1)
    resp.raise_for_status()
    return resp.json()


def fetch_file_nodes(file_key: str, node_ids: list[str], headers: dict) -> dict:
    """获取指定节点的详细信息"""
    ids = ",".join(node_ids)
    url = f"{FIGMA_API_BASE}/files/{file_key}/nodes?ids={ids}"
    resp = requests.get(url, headers=headers, timeout=60)
    resp.raise_for_status()
    return resp.json()


def fetch_file_images(file_key: str, node_ids: list[str], headers: dict) -> dict:
    """获取节点的图片导出链接"""
    ids = ",".join(node_ids)
    url = f"{FIGMA_API_BASE}/images/{file_key}?ids={ids}&format=png&scale=1"
    resp = requests.get(url, headers=headers, timeout=30)
    resp.raise_for_status()
    return resp.json()


# ============================================================
# 设计元素提取
# ============================================================

def extract_node_info(node: dict, depth: int = 0) -> dict | None:
    """递归提取节点关键信息"""
    if not isinstance(node, dict):
        return None

    node_type = node.get("type", "")
    node_name = node.get("name", "")

    # 跳过过于底层的几何节点，聚焦于有意义的设计元素
    if node_type in ("VECTOR", "LINE", "ELLIPSE", "POLYGON", "STAR") and depth > 3:
        return None

    info = {
        "id": node.get("id", ""),
        "name": node_name,
        "type": node_type,
        "visible": node.get("visible", True),
    }

    # 提取约束信息
    constraints = node.get("constraints", {})
    if constraints:
        info["constraints"] = constraints

    # 提取相对位置信息
    bbox = node.get("absoluteBoundingBox", {})
    if bbox:
        info["position"] = {
            "x": round(bbox.get("x", 0), 1),
            "y": round(bbox.get("y", 0), 1),
        }
        info["size"] = {
            "width": round(bbox.get("width", 0), 1),
            "height": round(bbox.get("height", 0), 1),
        }

    # 填充颜色（背景色）
    fills = node.get("fills", [])
    if fills and isinstance(fills, list):
        solid_fills = [f for f in fills if f.get("type") == "SOLID" and f.get("visible", True)]
        if solid_fills:
            color = solid_fills[0].get("color", {})
            info["background_color"] = {
                "r": round(color.get("r", 0) * 255),
                "g": round(color.get("g", 0) * 255),
                "b": round(color.get("b", 0) * 255),
                "a": round(color.get("a", 1), 2),
            }

    # 文本内容
    if node_type == "TEXT":
        info["text"] = node.get("characters", "")
        style = node.get("style", {})
        if style:
            info["text_style"] = {
                "font_family": style.get("fontFamily", ""),
                "font_size": style.get("fontSize", ""),
                "font_weight": style.get("fontWeight", ""),
                "text_align": style.get("textAlignHorizontal", ""),
                "line_height": style.get("lineHeightPx", ""),
            }

    # 组件/实例引用
    if node_type == "COMPONENT":
        info["component_property_definitions"] = node.get("componentPropertyDefinitions", {})

    if node_type == "INSTANCE":
        info["main_component"] = node.get("mainComponent", {})

    # 交互设置
    interactions = node.get("interactions", [])
    if interactions:
        info["interactions"] = [
            {
                "trigger": i.get("trigger", {}).get("type", ""),
                "action": i.get("action", {}).get("type", ""),
                "destination": i.get("action", {}).get("destinationId", ""),
            }
            for i in interactions if isinstance(i, dict)
        ]

    return info


def traverse_canvases(document: dict) -> list[dict]:
    """遍历文档的所有 Canvas（页面）和 Frame（画板）"""
    canvases = []
    children = document.get("children", [])
    for child in children:
        if child.get("type") in ("CANVAS", "FRAME", "GROUP"):
            canvas_info = extract_node_info(child)
            if canvas_info:
                frames = []
                for frame_node in child.get("children", []):
                    frame_info = extract_node_info(frame_node)
                    if frame_info:
                        sub_elements = _collect_visible_elements(frame_node)
                        frame_info["elements"] = sub_elements
                        frames.append(frame_info)
                canvas_info["frames"] = frames
                canvases.append(canvas_info)
    return canvases


def _collect_visible_elements(node: dict, depth: int = 0, max_depth: int = 5) -> list[dict]:
    """递归收集可见子元素"""
    if depth > max_depth:
        return []
    elements = []
    for child in node.get("children", []):
        info = extract_node_info(child, depth)
        if info and info.get("visible", True):
            # 继续递归收集更深层元素
            sub_elements = _collect_visible_elements(child, depth + 1, max_depth)
            if sub_elements:
                info["children"] = sub_elements
            elements.append(info)
    return elements


def extract_components(document: dict) -> list[dict]:
    """提取文档中所有组件（COMPONENT 和 COMPONENT_SET）"""
    components = []

    def _walk(node):
        if not isinstance(node, dict):
            return
        node_type = node.get("type", "")
        if node_type in ("COMPONENT", "COMPONENT_SET"):
            components.append(extract_node_info(node))
        for child in node.get("children", []):
            _walk(child)

    _walk(document)
    return components


def extract_styles(file_data: dict) -> list[dict]:
    """提取文件中的样式定义"""
    styles = file_data.get("styles", {})
    result = []
    for style_id, style_info in styles.items():
        result.append({
            "style_id": style_id,
            "name": style_info.get("name", ""),
            "type": style_info.get("styleType", ""),
            "description": style_info.get("description", ""),
        })
    return result


# ============================================================
# 主流程
# ============================================================

def build_design_summary(file_info: dict, canvases: list[dict], components: list[dict]) -> dict:
    """构建设计概要（供 Claude 阅读的结构化摘要）"""
    name = file_info.get("name", "")
    pages = []
    for canvas in canvases:
        page_info = {
            "page_name": canvas.get("name", ""),
            "page_type": canvas.get("type", ""),
            "frames": [],
        }
        for frame in canvas.get("frames", []):
            frame_info = {
                "frame_name": frame.get("name", ""),
                "size": frame.get("size", {}),
                "elements": [],
            }
            for elem in frame.get("elements", []):
                frame_info["elements"].append({
                    "name": elem.get("name", ""),
                    "type": elem.get("type", ""),
                    "text": elem.get("text", "") if elem.get("type") == "TEXT" else None,
                    "size": elem.get("size", {}),
                    "position": elem.get("position", {}),
                    "children_count": len(elem.get("children", [])),
                })
            page_info["frames"].append(frame_info)
        pages.append(page_info)

    return {
        "file_name": name,
        "pages": pages,
        "total_components": len(components),
        "component_names": [c.get("name", "") for c in components if c],
    }


def main():
    parser = argparse.ArgumentParser(description="从 Figma 获取 UI 设计信息")
    parser.add_argument("--url", required=True, help="Figma 文件的完整 URL")
    parser.add_argument("--output", "-o", help="输出 JSON 文件路径")
    parser.add_argument("--summary", "-s", help="输出文本摘要文件路径（Claude 可直接阅读）")
    args = parser.parse_args()

    headers = build_headers()
    file_key, node_id = parse_figma_url(args.url)

    # 获取文件信息
    print(f"正在获取 Figma 文件: {file_key} ...", file=sys.stderr)
    file_data = fetch_file_info(file_key, headers)
    document = file_data.get("document", {})

    # 提取结构化信息
    canvases = traverse_canvases(document)
    components = extract_components(document)
    styles = extract_styles(file_data)

    # 构建概要
    summary = build_design_summary(file_data, canvases, components)

    # 构建完整输出
    result = {
        "file_name": file_data.get("name", ""),
        "last_modified": file_data.get("lastModified", ""),
        "version": file_data.get("version", ""),
        "thumbnail_url": file_data.get("thumbnailUrl", ""),
        "canvases": canvases,
        "components": components,
        "styles": styles,
        "design_summary": summary,
    }

    # 输出
    output = json.dumps(result, ensure_ascii=False, indent=2)

    if args.output:
        os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output)
        print(f"JSON 已写入: {args.output}", file=sys.stderr)

    if args.summary:
        os.makedirs(os.path.dirname(args.summary) or ".", exist_ok=True)
        with open(args.summary, "w", encoding="utf-8") as f:
            f.write(f"# Figma 设计摘要: {summary['file_name']}\n\n")
            f.write(f"页面数: {len(summary['pages'])}\n")
            f.write(f"组件数: {summary['total_components']}\n")
            f.write(f"组件列表: {', '.join(summary['component_names'])}\n\n")
            for page in summary['pages']:
                f.write(f"## {page['page_name']}\n")
                for frame in page['frames']:
                    size = frame.get('size', {})
                    f.write(f"  - {frame['frame_name']} ({size.get('width', '?')}×{size.get('height', '?')}): {len(frame['elements'])} 个可见元素\n")
                    for elem in frame['elements']:
                        text = f" → \"{elem['text'][:50]}\"" if elem.get('text') else ""
                        f.write(f"    - [{elem['type']}] {elem['name']}{text}\n")
            f.write("\n")
        print(f"摘要已写入: {args.summary}", file=sys.stderr)

    if not args.output and not args.summary:
        print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
