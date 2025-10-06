"""Escaping helpers shared across output formatters."""

from __future__ import annotations

import unicodedata
from typing import Any

__all__ = [
    "escape_markdown_text",
    "fenced_block",
    "indent_block_lines",
    "max_backtick_run",
    "prepare_markdown_text",
]


def max_backtick_run(text: str) -> int:
    """Return the longest consecutive run of backticks in ``text``."""

    longest = 0
    current = 0
    for char in text:
        if char == "`":
            current += 1
            if current > longest:
                longest = current
        else:
            current = 0
    return longest


def indent_block_lines(text: str, indent: str) -> str:
    """Indent ``text`` for Markdown code blocks without losing control bytes."""

    if text == "":
        return indent
    segments = text.splitlines(keepends=True)
    if not segments:
        segments = [""]
    indented: list[str] = []
    for segment in segments:
        if segment:
            indented.append(f"{indent}{segment}")
        else:
            indented.append(indent)
    return "".join(indented)


def fenced_block(prefix: str, text: str, *, language: str = "text") -> list[str]:
    """Return Markdown fence lines for ``text`` with the provided ``prefix``."""

    fence_length = max(3, max_backtick_run(text) + 1)
    fence = "`" * fence_length
    opening = f"{prefix}{fence}{language}" if language else f"{prefix}{fence}"
    indent = " " * len(prefix)
    closing = f"{indent}{fence}"
    body = indent_block_lines(text, indent)
    return [opening, body, closing]


def escape_markdown_text(value: str) -> tuple[str, bool]:
    """Escape control characters for safe Markdown rendering."""

    sanitized_chars: list[str] = []
    needs_block = False
    for char in value:
        code_point = ord(char)
        category = unicodedata.category(char)
        if char == "\n":
            sanitized_chars.append(char)
            needs_block = True
            continue
        if char == "\r":
            sanitized_chars.append("\\u000d")
            needs_block = True
            continue
        if char == "\t":
            sanitized_chars.append("\\u0009")
            needs_block = True
            continue
        if char in {"\u2028", "\u2029"}:
            sanitized_chars.append(f"\\u{code_point:04x}")
            needs_block = True
            continue
        if category in {"Cc", "Cf"} or code_point == 0x7F:
            sanitized_chars.append(f"\\u{code_point:04x}")
            needs_block = True
        else:
            sanitized_chars.append(char)
    sanitized = "".join(sanitized_chars)
    if sanitized and not sanitized.strip():
        sanitized = "".join(f"\\u{ord(char):04x}" for char in value)
        needs_block = True
    return sanitized, needs_block


def prepare_markdown_text(
    value: Any, *, block_multiline: bool = False
) -> tuple[str, bool, bool]:
    """Return sanitized text, a block flag, and a placeholder marker."""

    if value is None:
        return "—", False, True
    text = str(value)
    if text == "":
        return "—", False, True
    sanitized, needs_block = escape_markdown_text(text)
    if block_multiline and any(ch in text for ch in ("\n", "\r", "\t")):
        needs_block = True
    if max_backtick_run(sanitized) >= 3:
        needs_block = True
    if sanitized == "":
        return "—", needs_block, True
    return sanitized, needs_block, False
