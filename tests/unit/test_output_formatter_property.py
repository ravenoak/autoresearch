"""Property tests for output formatter.

See `docs/specification.md` and
`docs/algorithms/output_format.md`.
"""

import json
import re
from hypothesis import HealthCheck, example, given, settings, strategies as st
from hypothesis.strategies import SearchStrategy

from autoresearch.output_format import OutputFormatter
from autoresearch.models import QueryResponse


_CONTROL_CODEPOINTS = [*range(0x00, 0x20), 0x7F]
_FORMAT_CODEPOINTS = [0x200B, 0xFEFF]
_ESCAPE_PATTERN = re.compile("\\\\u([0-9a-fA-F]{4})")


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


def _extract_block(section: str, indent: str = "") -> str:
    """Return the raw contents of a fenced code block."""

    marker = "```text"
    start = section.find(marker)
    if start == -1:
        return ""
    start = section.find("\n", start)
    if start == -1:
        return ""
    start += 1
    closing = f"\n{indent}```"
    end = section.find(closing, start)
    if end == -1:
        end = len(section)
    body = section[start:end]
    return _strip_indent_preserving(body, indent)


def _decode_value(section: str) -> str:
    """Decode a scalar value section back to its original text."""

    block = _extract_block(section)
    if block:
        return _decode_sanitized(block)
    text = section
    if text.startswith("\n"):
        text = text[1:]
    text = text.rstrip("\n")
    return _decode_sanitized(text)


def _decode_bullets(section: str) -> list[str]:
    """Decode a Markdown bullet list back to the original sequence."""

    lines = section.splitlines(keepends=True)
    items: list[str] = []
    idx = 0
    while idx < len(lines):
        line = lines[idx]
        if not line.strip():
            idx += 1
            continue
        if line.startswith("- ```text"):
            idx += 1
            block_lines: list[str] = []
            while idx < len(lines) and not lines[idx].startswith("  ```"):
                block_lines.append(lines[idx])
                idx += 1
            body = _strip_indent_preserving("".join(block_lines), "  ")
            if body.endswith("\n"):
                body = body[:-1]
            if idx < len(lines) and lines[idx].startswith("  ```"):
                idx += 1
            items.append(_decode_sanitized(body))
            continue
        if line.startswith("- "):
            content = line[2:]
            if content.endswith("\n"):
                content = content[:-1]
            items.append(_decode_sanitized(content))
        idx += 1
    return items


def _decode_numbered(section: str) -> list[str]:
    """Decode a numbered Markdown list back to the original sequence."""

    lines = section.splitlines(keepends=True)
    items: list[str] = []
    idx = 0
    while idx < len(lines):
        line = lines[idx]
        if not line.strip():
            idx += 1
            continue
        if ". ```text" in line:
            idx += 1
            block_lines: list[str] = []
            while idx < len(lines) and not lines[idx].startswith("   ```"):
                block_lines.append(lines[idx])
                idx += 1
            body = _strip_indent_preserving("".join(block_lines), "   ")
            if body.endswith("\n"):
                body = body[:-1]
            if idx < len(lines) and lines[idx].startswith("   ```"):
                idx += 1
            items.append(_decode_sanitized(body))
            continue
        if ". " in line:
            content = line.split(". ", 1)[1]
            if content.endswith("\n"):
                content = content[:-1]
            items.append(_decode_sanitized(content))
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
@given(
    answer=_edge_text(),
    citations=st.lists(_edge_text(max_size=15), min_size=1, max_size=3),
    reasoning=st.lists(_edge_text(max_size=15), min_size=1, max_size=3),
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
