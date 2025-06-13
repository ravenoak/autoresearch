import json
import pytest
from autoresearch.models import QueryResponse
from autoresearch.output_format import OutputFormatter


def test_format_json(capsys):
    resp = QueryResponse(
        answer="a", citations=["c"], reasoning=["r"], metrics={"m": 1}
    )
    OutputFormatter.format(resp, "json")
    captured = capsys.readouterr().out
    data = json.loads(captured)
    assert data["answer"] == "a"
    assert data["citations"] == ["c"]
    assert data["reasoning"] == ["r"]
    assert data["metrics"] == {"m": 1}


def test_format_markdown(capsys):
    resp = QueryResponse(
        answer="a", citations=["c"], reasoning=["r"], metrics={"m": 1}
    )
    OutputFormatter.format(resp, "markdown")
    captured = capsys.readouterr().out
    assert captured.startswith("# Answer")
    assert "## Citations" in captured
    assert "- c" in captured
    assert "## Reasoning" in captured
    assert "## Metrics" in captured


def test_format_plain(capsys):
    resp = QueryResponse(
        answer="a", citations=["c"], reasoning=["r"], metrics={"m": 1}
    )
    OutputFormatter.format(resp, "plain")
    captured = capsys.readouterr().out
    assert captured.startswith("Answer:")
    assert "Citations:" in captured
    assert "- c" not in captured
    assert "#" not in captured


def test_format_text_alias(capsys):
    resp = QueryResponse(
        answer="a", citations=["c"], reasoning=["r"], metrics={"m": 1}
    )
    OutputFormatter.format(resp, "text")
    captured = capsys.readouterr().out
    assert captured.startswith("Answer:")


def test_json_no_ansi(capsys):
    resp = QueryResponse(
        answer="a", citations=["c"], reasoning=["r"], metrics={"m": 1}
    )
    OutputFormatter.format(resp, "json")
    out = capsys.readouterr().out
    assert "\x1b[" not in out


def test_markdown_no_ansi(capsys):
    resp = QueryResponse(
        answer="a", citations=["c"], reasoning=["r"], metrics={"m": 1}
    )
    OutputFormatter.format(resp, "markdown")
    out = capsys.readouterr().out
    assert "\x1b[" not in out


@pytest.mark.parametrize(
    "fmt, start",
    [
        ("json", "{"),
        ("markdown", "# Answer"),
        ("plain", "Answer:"),
    ],
)
def test_format_dict_input(fmt, start, capsys):
    data = {
        "answer": "a",
        "citations": ["c"],
        "reasoning": ["r"],
        "metrics": {"m": 1},
    }
    OutputFormatter.format(data, fmt)
    out = capsys.readouterr().out
    assert out.startswith(start)
