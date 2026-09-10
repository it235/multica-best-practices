"""HTML to Markdown converter.

Uses ``markdownify`` when available for high-fidelity conversion, with a
hand-written fallback (extracted from the original main.py) when the package
isn't installed. Confluence-specific macros (drawio / code / panel / image) are
always handled here so the markdown output matches Confluence semantics.
"""

from __future__ import annotations

import re
from typing import Dict, Optional


try:
    from markdownify import markdownify as _markdownify  # type: ignore
    _HAS_MARKDOWNIFY = True
except Exception:
    _HAS_MARKDOWNIFY = False


class HTMLToMarkdownConverter:
    """Convert Confluence storage-format HTML to Markdown."""

    def __init__(self) -> None:
        self.attachment_map: Dict[str, str] = {}

    def convert(self, html_content: str, attachment_map: Optional[Dict[str, str]] = None) -> str:
        if not html_content:
            return ""
        self.attachment_map = attachment_map or {}

        # Pre-process Confluence-specific macros (must run before markdownify
        # because it doesn't understand <ac:*> tags).
        content = self._handle_confluence_macros(html_content)
        content = self._handle_attachment_images(content)

        if _HAS_MARKDOWNIFY:
            md = _markdownify(content, heading_style="ATX", bullets="-")
            return re.sub(r"\n{3,}", "\n\n", md).strip()

        # Fallback: legacy hand-rolled converter
        return self._legacy_convert(content)

    # ------------------------------------------------------------------ macros

    def _handle_confluence_macros(self, content: str) -> str:
        # drawio diagrams -> placeholder image link
        content = re.sub(
            r'<ac:structured-macro[^>]*ac:name=["\']drawio["\'][^>]*>.*?</ac:structured-macro>',
            "\n![diagram](attachments/diagram.png)\n",
            content,
            flags=re.DOTALL | re.IGNORECASE,
        )
        # Code macro - support optional language parameter
        def _code_repl(match: re.Match) -> str:
            lang_match = re.search(
                r'<ac:parameter[^>]*ac:name=["\']language["\'][^>]*>(.*?)</ac:parameter>',
                match.group(0), flags=re.DOTALL | re.IGNORECASE,
            )
            lang = (lang_match.group(1).strip() if lang_match else "")
            body_match = re.search(
                r'<ac:plain-text-body>\s*<!\[CDATA\[(.*?)\]\]>\s*</ac:plain-text-body>',
                match.group(0), flags=re.DOTALL,
            )
            body = body_match.group(1) if body_match else ""
            return f"\n```{lang}\n{body}\n```\n"

        content = re.sub(
            r'<ac:structured-macro[^>]*ac:name=["\']code["\'][^>]*>.*?</ac:structured-macro>',
            _code_repl, content, flags=re.DOTALL | re.IGNORECASE,
        )

        # info / note / warning / tip panels -> blockquotes
        for panel in ("info", "note", "warning", "tip"):
            content = re.sub(
                rf'<ac:structured-macro[^>]*ac:name=["\']({panel})["\'][^>]*>.*?'
                rf'<ac:rich-text-body>(.*?)</ac:rich-text-body>\s*</ac:structured-macro>',
                rf"\n> **\1:** \2\n",
                content, flags=re.DOTALL | re.IGNORECASE,
            )
        return content

    def _handle_attachment_images(self, content: str) -> str:
        """Rewrite <ac:image><ri:attachment ri:filename="x.png"/></ac:image>."""

        def repl(match: re.Match) -> str:
            filename = match.group(1)
            rel_path = self.attachment_map.get(filename, f"attachments/{filename}")
            return f"![{filename}]({rel_path})"

        content = re.sub(
            r'<ac:image[^>]*>\s*<ri:attachment[^>]*ri:filename=["\']([^"\']+)["\'][^/]*/>\s*</ac:image>',
            repl, content, flags=re.DOTALL | re.IGNORECASE,
        )
        # Also rewrite <ri:attachment> referenced as plain links
        content = re.sub(
            r'<ri:attachment[^>]*ri:filename=["\']([^"\']+)["\'][^/]*/>',
            lambda m: self.attachment_map.get(m.group(1), f"attachments/{m.group(1)}"),
            content, flags=re.IGNORECASE,
        )
        return content

    # ----------------------------------------------------------- legacy fallback

    def _legacy_convert(self, content: str) -> str:
        for i in range(6, 0, -1):
            content = re.sub(
                rf"<h{i}[^>]*>(.*?)</h{i}>",
                lambda m, lvl=i: "#" * lvl + " " + self._strip_tags(m.group(1)) + "\n\n",
                content, flags=re.DOTALL | re.IGNORECASE,
            )
        content = re.sub(r"<p[^>]*>(.*?)</p>", r"\1\n\n", content, flags=re.DOTALL | re.IGNORECASE)
        content = re.sub(r"<strong[^>]*>(.*?)</strong>", r"**\1**", content, flags=re.DOTALL | re.IGNORECASE)
        content = re.sub(r"<b[^>]*>(.*?)</b>", r"**\1**", content, flags=re.DOTALL | re.IGNORECASE)
        content = re.sub(r"<em[^>]*>(.*?)</em>", r"*\1*", content, flags=re.DOTALL | re.IGNORECASE)
        content = re.sub(r"<i[^>]*>(.*?)</i>", r"*\1*", content, flags=re.DOTALL | re.IGNORECASE)
        content = re.sub(r"<code[^>]*>(.*?)</code>", r"`\1`", content, flags=re.DOTALL | re.IGNORECASE)
        content = re.sub(
            r'<a[^>]*href=["\']([^"\']*)["\'][^>]*>(.*?)</a>',
            r"[\2](\1)", content, flags=re.DOTALL | re.IGNORECASE,
        )
        content = self._convert_list(content, "ul", "-")
        content = self._convert_ordered_list(content)
        content = self._convert_table(content)
        content = re.sub(r"<br\s*/?>", "\n", content, flags=re.IGNORECASE)
        content = re.sub(r"<hr\s*/?>", "\n---\n", content, flags=re.IGNORECASE)
        content = self._strip_tags(content)
        return re.sub(r"\n{3,}", "\n\n", content).strip()

    def _convert_list(self, content: str, tag: str, marker: str) -> str:
        def process_list(match: re.Match) -> str:
            items = re.findall(r"<li[^>]*>(.*?)</li>", match.group(1), re.DOTALL | re.IGNORECASE)
            return "\n".join(f"{marker} {self._strip_tags(item).strip()}" for item in items) + "\n\n"
        return re.sub(rf"<{tag}[^>]*>(.*?)</{tag}>", process_list, content, flags=re.DOTALL | re.IGNORECASE)

    def _convert_ordered_list(self, content: str) -> str:
        def process_list(match: re.Match) -> str:
            items = re.findall(r"<li[^>]*>(.*?)</li>", match.group(1), re.DOTALL | re.IGNORECASE)
            return "\n".join(f"{i}. {self._strip_tags(item).strip()}" for i, item in enumerate(items, 1)) + "\n\n"
        return re.sub(r"<ol[^>]*>(.*?)</ol>", process_list, content, flags=re.DOTALL | re.IGNORECASE)

    def _convert_table(self, content: str) -> str:
        def process_table(match: re.Match) -> str:
            rows = re.findall(r"<tr[^>]*>(.*?)</tr>", match.group(1), re.DOTALL | re.IGNORECASE)
            if not rows:
                return ""
            md_rows = []
            for row in rows:
                cells = re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", row, re.DOTALL | re.IGNORECASE)
                if cells:
                    clean = [self._strip_tags(c).strip().replace("|", "\\|") for c in cells]
                    md_rows.append("| " + " | ".join(clean) + " |")
            return "\n" + "\n".join(md_rows) + "\n\n"
        return re.sub(r"<table[^>]*>(.*?)</table>", process_table, content, flags=re.DOTALL | re.IGNORECASE)

    def _strip_tags(self, text: str) -> str:
        text = re.sub(r"<!\[CDATA\[(.*?)\]\]>", r"\1", text, flags=re.DOTALL)
        text = re.sub(r"<[^>]+>", "", text)
        for entity, char in {"&nbsp;": " ", "&amp;": "&", "&lt;": "<", "&gt;": ">", "&quot;": '"'}.items():
            text = text.replace(entity, char)
        return text
