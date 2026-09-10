"""Markdown to Confluence Storage Format converter.

Handles the common Markdown subset produced by AI/developers:
  - Headings (h1-h6)
  - Bold / italic / inline code
  - Fenced code blocks (with optional language)
  - Unordered & ordered lists (nested up to 2 levels)
  - Links & images
  - Blockquotes
  - Horizontal rules
  - Tables (GFM pipe tables)
  - Paragraphs

Does NOT rely on any third-party library.
"""

from __future__ import annotations

import re
from typing import List, Tuple


# ────────────────────────────────────────────────── helpers

_FENCE_RE = re.compile(r"^(`{3,}|~{3,})\s*(\w*)\s*$")
_HEADING_RE = re.compile(r"^(#{1,6})\s+(.+)$")
_HR_RE = re.compile(r"^[-*_]{3,}\s*$")
_UL_RE = re.compile(r"^(\s*)[*\-+]\s+(.+)$")
_OL_RE = re.compile(r"^(\s*)\d+\.\s+(.+)$")
_BLOCKQUOTE_RE = re.compile(r"^>\s?(.*)")
_TABLE_SEP_RE = re.compile(r"^\|?(\s*:?-+:?\s*\|)+\s*:?-+:?\s*\|?\s*$")
_TABLE_ROW_RE = re.compile(r"^\|(.+)\|$")


def _inline(text: str) -> str:
    """Convert inline Markdown to Confluence XHTML."""
    # Escape XML special characters FIRST (order: & before < >)
    text = text.replace("&", "&amp;")
    text = text.replace("<", "&lt;")
    text = text.replace(">", "&gt;")
    # Images: ![alt](src)
    text = re.sub(
        r"!\[([^\]]*)\]\(([^)]+)\)",
        r'<ac:image><ri:url ri:value="\2"/></ac:image>',
        text,
    )
    # Links: [text](url)
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', text)
    # Bold: **text** or __text__
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"__(.+?)__", r"<strong>\1</strong>", text)
    # Italic: *text* or _text_  (but not inside URLs/words)
    text = re.sub(r"(?<!\w)\*([^*]+?)\*(?!\w)", r"<em>\1</em>", text)
    text = re.sub(r"(?<!\w)_([^_]+?)_(?!\w)", r"<em>\1</em>", text)
    # Inline code: `code`
    text = re.sub(r"`([^`]+?)`", r"<code>\1</code>", text)
    # Escape special Confluence chars: { } — only bare ones
    text = text.replace("{", "&#123;").replace("}", "&#125;")
    return text


def _extract_title(lines: List[str]) -> Tuple[str, List[str]]:
    """Extract first H1 as document title; return (title, remaining_lines)."""
    for i, line in enumerate(lines):
        m = _HEADING_RE.match(line)
        if m and len(m.group(1)) == 1:
            return m.group(2).strip(), lines[:i] + lines[i + 1:]
    return "", lines


def _strip_frontmatter(lines: List[str]) -> List[str]:
    """Remove YAML frontmatter (--- ... ---) if present."""
    if not lines or lines[0].strip() != "---":
        return lines
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            return lines[i + 1:]
    return lines


# ────────────────────────────────────────────────── block-level parser

class MarkdownToConfluenceConverter:
    """Stateful block parser that emits Confluence storage-format XHTML."""

    AI_SUFFIX = " [AI]"

    def convert(self, markdown_text: str, title_override: str | None = None) -> Tuple[str, str]:
        """Convert markdown to (title, storage_format_body).

        Title is derived from the first H1, or title_override if given.
        The AI suffix is appended to the title automatically.
        """
        lines = markdown_text.replace("\r\n", "\n").split("\n")
        lines = _strip_frontmatter(lines)
        extracted_title, lines = _extract_title(lines)

        title = (title_override or extracted_title or "Untitled").strip()
        if not title.endswith(self.AI_SUFFIX):
            title += self.AI_SUFFIX

        body = self._parse_blocks(lines)
        return title, body

    # ──────────────────────────────────────── block dispatcher

    def _parse_blocks(self, lines: List[str]) -> str:
        out: List[str] = []
        i = 0
        n = len(lines)

        while i < n:
            line = lines[i]

            # Fenced code block
            fence = _FENCE_RE.match(line)
            if fence:
                lang = fence.group(2) or "none"
                fence_marker = fence.group(1)
                code_lines: List[str] = []
                i += 1
                while i < n and not lines[i].startswith(fence_marker):
                    code_lines.append(lines[i])
                    i += 1
                i += 1  # skip closing fence
                code = "\n".join(code_lines)
                escaped_code = (
                    code.replace("&", "&amp;")
                    .replace("<", "&lt;")
                    .replace(">", "&gt;")
                )
                out.append(
                    f'<ac:structured-macro ac:name="code">'
                    f'<ac:parameter ac:name="language">{lang}</ac:parameter>'
                    f'<ac:plain-text-body><![CDATA[{code}]]></ac:plain-text-body>'
                    f'</ac:structured-macro>'
                )
                continue

            # Heading
            hm = _HEADING_RE.match(line)
            if hm:
                level = len(hm.group(1))
                text = _inline(hm.group(2).strip())
                out.append(f"<h{level}>{text}</h{level}>")
                i += 1
                continue

            # Horizontal rule
            if _HR_RE.match(line):
                out.append("<hr/>")
                i += 1
                continue

            # Table
            if _TABLE_ROW_RE.match(line):
                table_lines: List[str] = []
                while i < n and (_TABLE_ROW_RE.match(lines[i]) or _TABLE_SEP_RE.match(lines[i])):
                    table_lines.append(lines[i])
                    i += 1
                out.append(self._render_table(table_lines))
                continue

            # Blockquote
            bq = _BLOCKQUOTE_RE.match(line)
            if bq:
                bq_lines: List[str] = []
                while i < n:
                    bqm = _BLOCKQUOTE_RE.match(lines[i])
                    if bqm:
                        bq_lines.append(bqm.group(1))
                        i += 1
                    elif lines[i].strip() == "":
                        break
                    else:
                        break
                inner = _inline(" ".join(bq_lines))
                out.append(f"<blockquote><p>{inner}</p></blockquote>")
                continue

            # Unordered list
            if _UL_RE.match(line):
                i = self._parse_list(lines, i, ordered=False, out=out)
                continue

            # Ordered list
            if _OL_RE.match(line):
                i = self._parse_list(lines, i, ordered=True, out=out)
                continue

            # Blank line
            if not line.strip():
                i += 1
                continue

            # Paragraph (collect contiguous non-blank lines)
            para: List[str] = []
            while i < n and lines[i].strip() and not _HEADING_RE.match(lines[i]) and not _FENCE_RE.match(lines[i]):
                para.append(lines[i])
                i += 1
            out.append(f"<p>{_inline(' '.join(para))}</p>")

        return "\n".join(out)

    # ──────────────────────────────────────── list helper

    def _parse_list(self, lines: List[str], start: int, ordered: bool, out: List[str]) -> int:
        tag = "ol" if ordered else "ul"
        pattern = _OL_RE if ordered else _UL_RE
        items: List[str] = []
        i = start
        n = len(lines)

        while i < n:
            m = pattern.match(lines[i])
            if m:
                items.append(_inline(m.group(2)))
                i += 1
            elif lines[i].startswith("  ") or lines[i].startswith("\t"):
                # continuation of previous item
                if items:
                    items[-1] += " " + _inline(lines[i].strip())
                i += 1
            else:
                break

        inner = "".join(f"<li>{it}</li>" for it in items)
        out.append(f"<{tag}>{inner}</{tag}>")
        return i

    # ──────────────────────────────────────── table helper

    def _render_table(self, table_lines: List[str]) -> str:
        rows: List[List[str]] = []
        for line in table_lines:
            if _TABLE_SEP_RE.match(line):
                continue
            cells = [c.strip() for c in line.strip("|").split("|")]
            rows.append(cells)

        if not rows:
            return ""

        parts: List[str] = ["<table>"]
        # First row as header
        parts.append("<thead><tr>")
        for cell in rows[0]:
            parts.append(f"<th>{_inline(cell)}</th>")
        parts.append("</tr></thead>")

        # Body
        if len(rows) > 1:
            parts.append("<tbody>")
            for row in rows[1:]:
                parts.append("<tr>")
                for cell in row:
                    parts.append(f"<td>{_inline(cell)}</td>")
                parts.append("</tr>")
            parts.append("</tbody>")

        parts.append("</table>")
        return "".join(parts)
