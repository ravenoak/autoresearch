"""Property tests for output formatter.

See `docs/specification.md` and
`docs/algorithms/output_format.md`.
"""

import json
import unicodedata

from hypothesis import HealthCheck, given, settings, strategies as st
from hypothesis.strategies import SearchStrategy

from autoresearch.output_format import OutputFormatter
from autoresearch.models import QueryResponse


_CONTROL_CODEPOINTS = [*range(0x00, 0x20), 0x7F]
_FORMAT_CODEPOINTS = [0x200B, 0xFEFF]


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

    return st.one_of(general_text, whitespace_only, _with_required_control())


def _escape_for_markdown(value: str, *, block_multiline: bool = False) -> tuple[str, bool]:
    """Mirror the formatter's sanitisation contract for assertions."""

    sanitized_chars: list[str] = []
    needs_block = False
    for char in value:
        if char in {"\n", "\r", "\t"}:
            sanitized_chars.append(char)
            continue
        code_point = ord(char)
        category = unicodedata.category(char)
        if category in {"Cc", "Cf"} or code_point == 0x7F:
            sanitized_chars.append(f"\\u{code_point:04x}")
            needs_block = True
        else:
            sanitized_chars.append(char)
    sanitized = "".join(sanitized_chars)
    if sanitized and not sanitized.strip():
        sanitized = "".join(f"\\u{ord(char):04x}" for char in value)
        needs_block = True
    if block_multiline and any(char in value for char in "\n\r\t"):
        needs_block = True
    return sanitized or "—", needs_block


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


def _bullet_block(sanitized: str) -> str:
    lines = sanitized.splitlines() or [""]
    indented = "\n".join(f"  {line}" if line else "  " for line in lines)
    return f"- ```text\n{indented}\n  ```"


def _numbered_block(index: int, sanitized: str) -> str:
    lines = sanitized.splitlines() or [""]
    indented = "\n".join(f"   {line}" if line else "   " for line in lines)
    return f"{index}. ```text\n{indented}\n   ```"


@settings(suppress_health_check=[HealthCheck.too_slow, HealthCheck.function_scoped_fixture])
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
    sanitized_answer, answer_block = _escape_for_markdown(answer)
    assert sanitized_answer in answer_section
    if answer_block:
        assert "```text" in answer_section

    citations_section = _section(md, "Citations")
    for citation in citations:
        sanitized_citation, citation_block = _escape_for_markdown(
            citation, block_multiline=True
        )
        if citation_block:
            assert _bullet_block(sanitized_citation) in citations_section
        else:
            assert f"- {sanitized_citation}" in citations_section

    reasoning_section = _section(md, "Reasoning Trace")
    for idx, step in enumerate(reasoning, start=1):
        sanitized_step, step_block = _escape_for_markdown(step, block_multiline=True)
        if step_block:
            assert _numbered_block(idx, sanitized_step) in reasoning_section
        else:
            assert f"{idx}. {sanitized_step}" in reasoning_section
