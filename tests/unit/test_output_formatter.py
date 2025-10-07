# mypy: ignore-errors
"""Property tests for output formatter.

See `docs/specification.md` and
`docs/algorithms/output_format.md`.
"""

import json
import re
from typing import List, Optional, Tuple

from hypothesis import HealthCheck, example, given, settings, strategies as st
from hypothesis.strategies import SearchStrategy

from autoresearch.output_format import (
    OutputFormatter,
    _PLACEHOLDER_EMPTY_MARKER,
    _PLACEHOLDER_NULL_MARKER,
)
from autoresearch.models import QueryResponse


_CONTROL_CODEPOINTS = [*range(0x00, 0x20), 0x7F]
_FORMAT_CODEPOINTS = [0x200B, 0xFEFF]
_ESCAPE_PATTERN = re.compile("\\\\u([0-9a-fA-F]{4})")
_FENCE_PATTERN = re.compile(r"^(?P<prefix>[^`]*)(?P<fence>`{3,})(?P<language>[A-Za-z0-9]*)$")

_PLACEHOLDER_MAP = {
    _PLACEHOLDER_NULL_MARKER: None,
    _PLACEHOLDER_EMPTY_MARKER: "",
}


def _strip_placeholder_marker(text: str) -> Tuple[str, Optional[str]]:
    """Remove placeholder markers appended by the formatter."""

    for marker in _PLACEHOLDER_MAP:
        if text.endswith(marker):
            return text[: -len(marker)], marker
    return text, None


def _edge_text(min_size: int = 1, max_size: int = 20) -> SearchStrategy[str]:
    """Return a strategy that covers printable, control, and whitespace cases."""

    printable = st.characters(
        min_codepoint=32,
        max_codepoint=0x10FFFF,
        blacklist_categories=("Cs",),
    )
    control_chars = st.sampled_from([chr(cp) for cp in _CONTROL_CODEPOINTS])
    format_chars = st.sampled_from([chr(cp) for cp in _FORMAT_CODEPOINTS])
    mixed_alphabet = st.one_of(printable, control_chars, format_chars)

    general_text = st.text(alphabet=mixed_alphabet, min_size=min_size, max_size=max_size)

    control_dense = st.lists(
        st.sampled_from([chr(cp) for cp in _CONTROL_CODEPOINTS]),
        min_size=1,
        max_size=max_size,
    ).map("".join)

    whitespace_pool = [
        " " * n for n in range(1, 5)
    ] + ["\t", "\n", "\r\n"] + ["\u200b" * n for n in range(1, 3)]
    whitespace_only = st.sampled_from(whitespace_pool)

    def _with_required_control() -> st.SearchStrategy[str]:
        prefix = st.text(alphabet=printable, min_size=0, max_size=max_size - 1)
        suffix = st.text(alphabet=printable, min_size=0, max_size=max_size - 1)
        special = st.one_of(control_chars, format_chars)
        return st.builds(
            lambda left, ch, right: f"{left}{ch}{right}" or ch,
            prefix,
            special,
            suffix,
        )

    return st.one_of(general_text, whitespace_only, _with_required_control(), control_dense)


def _decode_sanitized(text: str) -> str:
    """Convert ``\\u`` escape sequences back to their original characters."""

    return _ESCAPE_PATTERN.sub(lambda match: chr(int(match.group(1), 16)), text)


def _strip_indent_preserving(text: str, indent: str) -> str:
    """Remove ``indent`` prefixes from each line while keeping newlines intact."""

    if not indent:
        return text
    lines = text.splitlines(keepends=True)
    if not lines:
        return ""
    return "".join(line[len(indent) :] if line.startswith(indent) else line for line in lines)


def _parse_fence(line: str) -> Optional[tuple[str, int]]:
    """Return the prefix and fence length for a Markdown code fence line."""

    stripped = line.rstrip("\n")
    match = _FENCE_PATTERN.match(stripped)
    if match is None:
        return None
    prefix = match.group("prefix")
    fence_length = len(match.group("fence"))
    return prefix, fence_length


def _extract_block(section: str) -> str:
    """Return the raw contents of the first fenced code block in ``section``."""

    lines = section.splitlines(keepends=True)
    for idx, line in enumerate(lines):
        parsed = _parse_fence(line)
        if parsed is None:
            continue
        prefix, fence_length = parsed
        indent = " " * len(prefix)
        closing = f"{indent}{'`' * fence_length}"
        body_lines: list[str] = []
        pointer = idx + 1
        while pointer < len(lines):
            candidate = lines[pointer]
            if candidate.rstrip("\n") == closing:
                break
            body_lines.append(candidate)
            pointer += 1
        body = "".join(body_lines)
        stripped = _strip_indent_preserving(body, indent)
        if stripped.endswith("\n"):
            stripped = stripped[:-1]
        return stripped
    return ""


def _decode_value(section: str) -> Optional[str]:
    """Decode a scalar value section back to its original text."""

    block = _extract_block(section)
    if block:
        stripped, marker = _strip_placeholder_marker(block)
        decoded = _decode_sanitized(stripped)
        if marker is not None:
            return _PLACEHOLDER_MAP[marker]
        return decoded
    text = section
    if text.startswith("\n"):
        text = text[1:]
    text = text.rstrip("\n")
    stripped, marker = _strip_placeholder_marker(text)
    decoded = _decode_sanitized(stripped)
    if marker is not None:
        return _PLACEHOLDER_MAP[marker]
    return decoded


def _decode_bullets(section: str) -> List[Optional[str]]:
    """Decode a Markdown bullet list back to the original sequence."""

    lines = section.splitlines(keepends=True)
    items: list[str] = []
    idx = 0
    while idx < len(lines):
        line = lines[idx]
        if not line.strip():
            idx += 1
            continue
        parsed = _parse_fence(line)
        if parsed is not None and parsed[0].startswith("- "):
            prefix, fence_length = parsed
            indent = " " * len(prefix)
            closing = f"{indent}{'`' * fence_length}"
            lookahead = idx + 1
            block_lines: list[str] = []
            while lookahead < len(lines) and lines[lookahead].rstrip("\n") != closing:
                block_lines.append(lines[lookahead])
                lookahead += 1
            if lookahead >= len(lines):
                content = line[len(prefix) :]
                if content.endswith("\n"):
                    content = content[:-1]
                stripped, marker = _strip_placeholder_marker(content)
                decoded = _decode_sanitized(stripped)
                items.append(_PLACEHOLDER_MAP[marker] if marker else decoded)
                idx += 1
                continue
            body = _strip_indent_preserving("".join(block_lines), indent)
            if body.endswith("\n"):
                body = body[:-1]
            idx = lookahead + 1
            stripped, marker = _strip_placeholder_marker(body)
            decoded = _decode_sanitized(stripped)
            items.append(_PLACEHOLDER_MAP[marker] if marker else decoded)
            continue
        if line.startswith("- "):
            content = line[2:]
            if content.endswith("\n"):
                content = content[:-1]
            stripped, marker = _strip_placeholder_marker(content)
            decoded = _decode_sanitized(stripped)
            items.append(_PLACEHOLDER_MAP[marker] if marker else decoded)
        idx += 1
    return items


def _decode_numbered(section: str) -> List[Optional[str]]:
    """Decode a numbered Markdown list back to the original sequence."""

    lines = section.splitlines(keepends=True)
    items: list[str] = []
    idx = 0
    while idx < len(lines):
        line = lines[idx]
        if not line.strip():
            idx += 1
            continue
        parsed = _parse_fence(line)
        if (
            parsed is not None
            and parsed[0].endswith(". ")
            and parsed[0][:-2].isdigit()
        ):
            prefix, fence_length = parsed
            indent = " " * len(prefix)
            closing = f"{indent}{'`' * fence_length}"
            lookahead = idx + 1
            block_lines: list[str] = []
            while lookahead < len(lines) and lines[lookahead].rstrip("\n") != closing:
                block_lines.append(lines[lookahead])
                lookahead += 1
            if lookahead >= len(lines):
                content = line.split(". ", 1)[1]
                if content.endswith("\n"):
                    content = content[:-1]
                stripped, marker = _strip_placeholder_marker(content)
                decoded = _decode_sanitized(stripped)
                items.append(_PLACEHOLDER_MAP[marker] if marker else decoded)
                idx += 1
                continue
            body = _strip_indent_preserving("".join(block_lines), indent)
            if body.endswith("\n"):
                body = body[:-1]
            idx = lookahead + 1
            stripped, marker = _strip_placeholder_marker(body)
            decoded = _decode_sanitized(stripped)
            items.append(_PLACEHOLDER_MAP[marker] if marker else decoded)
            continue
        if ". " in line:
            content = line.split(". ", 1)[1]
            if content.endswith("\n"):
                content = content[:-1]
            stripped, marker = _strip_placeholder_marker(content)
            decoded = _decode_sanitized(stripped)
            items.append(_PLACEHOLDER_MAP[marker] if marker else decoded)
        idx += 1
    return items


def _section(markdown: str, header: str) -> str:
    """Extract the body of a second-level Markdown section."""

    marker = f"## {header}"
    start = markdown.find(marker)
    if start == -1:
        return ""
    start = markdown.find("\n", start)
    if start == -1:
        return ""
    start += 1
    next_header = markdown.find("\n## ", start)
    if next_header == -1:
        return markdown[start:]
    return markdown[start:next_header]


@settings(suppress_health_check=[HealthCheck.too_slow, HealthCheck.function_scoped_fixture])
@example(
    answer="\u0000core\r\n",
    citations=["\talpha", "beta\u0002"],
    reasoning=["lead\ntrail", "\u0007"],
)
@example(
    answer="\u2028split",
    citations=["only\r", "\u200b"],
    reasoning=["\u000bbranch"],
)
@example(
    answer="tick```tick",
    citations=["prefix````suffix", "plain"],
    reasoning=["wrap`````wrap", "steady"],
)
@example(
    answer="\u2029para",
    citations=["lead\u2028line"],
    reasoning=["mix```multi", "tab\ttrail"],
)
@example(
    answer="```",
    citations=["```"],
    reasoning=["```"],
)
@example(
    answer="tab\tanchor",
    citations=[None, "dual\nline"],
    reasoning=["```\nblock\n```", None],
)
@example(
    answer="pre```\ncode\n```post",
    citations=["fence````wrap", "multi\n```\nclose"],
    reasoning=["step1", "wrap```\ninner\n```tail"],
)
@given(
    answer=_edge_text(),
    citations=st.lists(
        st.one_of(st.none(), _edge_text(max_size=15)), min_size=1, max_size=3
    ),
    reasoning=st.lists(
        st.one_of(st.none(), _edge_text(max_size=15)), min_size=1, max_size=3
    ),
)
def test_output_formatter_json_markdown(answer, citations, reasoning, capsys):
    resp = QueryResponse(answer=answer, citations=citations, reasoning=reasoning, metrics={})
    OutputFormatter.format(resp, "json")
    parsed = json.loads(capsys.readouterr().out)
    assert parsed["answer"] == answer
    assert parsed["citations"] == citations
    assert parsed["reasoning"] == reasoning

    OutputFormatter.format(resp, "markdown")
    md = capsys.readouterr().out
    answer_section = _section(md, "Answer")
    assert _decode_value(answer_section) == answer

    citations_section = _section(md, "Citations")
    assert _decode_bullets(citations_section) == citations

    reasoning_section = _section(md, "Reasoning Trace")
    assert _decode_numbered(reasoning_section) == reasoning
