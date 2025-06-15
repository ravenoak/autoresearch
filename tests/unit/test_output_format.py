import json
import pytest
from autoresearch.models import QueryResponse
from autoresearch.output_format import OutputFormatter
from pydantic import ValidationError
from autoresearch.errors import ValidationError as AutoresearchValidationError


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


def test_format_invalid_input():
    """Test that an invalid input raises an AutoresearchValidationError."""
    # Create an invalid input
    invalid_input = {"wrong_field": "value"}

    # Verify that an AutoresearchValidationError is raised
    with pytest.raises(AutoresearchValidationError):
        OutputFormatter.format(invalid_input, "json")


def test_format_unknown_defaults_to_markdown(capsys):
    """Test that unknown format types default to Markdown."""
    resp = QueryResponse(
        answer="a", citations=["c"], reasoning=["r"], metrics={"m": 1}
    )
    OutputFormatter.format(resp, "unknown")
    captured = capsys.readouterr().out
    assert captured.startswith("# Answer")
    assert "## Citations" in captured


def test_format_complex_response(capsys):
    """Test that the format method correctly handles a complex QueryResponse."""
    resp = QueryResponse(
        answer="This is a complex answer with multiple paragraphs.\n\nSecond paragraph.",
        citations=["Citation 1", "Citation 2 with [link](https://example.com)"],
        reasoning=["Reasoning step 1", "Reasoning step 2 with *emphasis*"],
        metrics={"tokens": 100, "time": 1.5, "sources": ["web", "knowledge_base"]}
    )
    OutputFormatter.format(resp, "markdown")
    captured = capsys.readouterr().out

    # Check answer formatting
    assert "# Answer" in captured
    assert "This is a complex answer with multiple paragraphs." in captured
    assert "Second paragraph." in captured

    # Check citations formatting
    assert "## Citations" in captured
    assert "- Citation 1" in captured
    assert "- Citation 2 with [link](https://example.com)" in captured

    # Check reasoning formatting
    assert "## Reasoning" in captured
    assert "- Reasoning step 1" in captured
    assert "- Reasoning step 2 with *emphasis*" in captured

    # Check metrics formatting
    assert "## Metrics" in captured
    assert "- **tokens**: 100" in captured
    assert "- **time**: 1.5" in captured
    assert "- **sources**: ['web', 'knowledge_base']" in captured
