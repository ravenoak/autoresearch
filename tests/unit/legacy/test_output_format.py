# mypy: ignore-errors
"""Output formatting tests.

Refer to `docs/specification.md` and
`docs/algorithms/output_format.md` for design details.
"""

import json
import tempfile
import logging
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
from autoresearch.models import QueryResponse
from autoresearch.output_format import (
    OutputDepth,
    OutputFormatter,
    FormatTemplate,
    TemplateRegistry,
)
from autoresearch.errors import ValidationError as AutoresearchValidationError


# Disable logging for tests
logging.getLogger("autoresearch.output_format").setLevel(logging.CRITICAL)


def test_format_json(capsys):
    resp = QueryResponse(answer="a", citations=["c"], reasoning=["r"], metrics={"m": 1})
    OutputFormatter.format(resp, "json")
    captured = capsys.readouterr().out
    data = json.loads(captured)
    assert data["answer"] == "a"
    assert data["citations"] == ["c"]
    assert data["reasoning"] == ["r"]
    assert data["metrics"] == {"m": 1}


def test_format_markdown(capsys):
    resp = QueryResponse(answer="a", citations=["c"], reasoning=["r"], metrics={"m": 1})
    OutputFormatter.format(resp, "markdown")
    captured = capsys.readouterr().out
    assert "# Answer" in captured
    assert "## Citations" in captured
    assert "- c" in captured
    assert "## Reasoning" in captured
    assert "## Metrics" in captured
    assert "## Task Graph" in captured
    assert "## ReAct Trace" in captured


def test_format_plain(capsys):
    resp = QueryResponse(answer="a", citations=["c"], reasoning=["r"], metrics={"m": 1})
    OutputFormatter.format(resp, "plain")
    captured = capsys.readouterr().out
    assert "Answer:" in captured
    assert "Citations:" in captured
    assert "- c" in captured  # Plain format now uses bullet points for citations
    assert "#" not in captured  # Still no markdown headings
    assert "Task Graph:" in captured
    assert "ReAct Trace:" in captured


def test_format_text_alias(capsys):
    resp = QueryResponse(answer="a", citations=["c"], reasoning=["r"], metrics={"m": 1})
    OutputFormatter.format(resp, "text")
    captured = capsys.readouterr().out
    assert "Answer:" in captured


def test_json_no_ansi(capsys):
    resp = QueryResponse(answer="a", citations=["c"], reasoning=["r"], metrics={"m": 1})
    OutputFormatter.format(resp, "json")
    out = capsys.readouterr().out
    assert "\x1b[" not in out


def test_markdown_no_ansi(capsys):
    resp = QueryResponse(answer="a", citations=["c"], reasoning=["r"], metrics={"m": 1})
    OutputFormatter.format(resp, "markdown")
    out = capsys.readouterr().out
    assert "\x1b[" not in out


def test_format_graph(capsys):
    resp = QueryResponse(answer="a", citations=["c"], reasoning=[], metrics={})
    OutputFormatter.format(resp, "graph")
    out = capsys.readouterr().out
    assert "Knowledge Graph" in out


@pytest.mark.parametrize(
    "fmt, content",
    [
        ("json", "{"),
        ("markdown", "# Answer"),
        ("plain", "Answer:"),
    ],
)
def test_format_dict_input(fmt, content, capsys):
    data = {
        "answer": "a",
        "citations": ["c"],
        "reasoning": ["r"],
        "metrics": {"m": 1},
    }
    OutputFormatter.format(data, fmt)
    out = capsys.readouterr().out
    assert content in out


def test_format_invalid_input():
    """Test that an invalid input raises an AutoresearchValidationError."""
    # Create an invalid input
    invalid_input = {"wrong_field": "value"}

    # Verify that an AutoresearchValidationError is raised
    with pytest.raises(AutoresearchValidationError):
        OutputFormatter.format(invalid_input, "json")


def test_format_unknown_defaults_to_markdown(capsys):
    """Test that unknown format types default to Markdown."""
    resp = QueryResponse(answer="a", citations=["c"], reasoning=["r"], metrics={"m": 1})
    OutputFormatter.format(resp, "unknown")
    captured = capsys.readouterr().out
    assert "# Answer" in captured
    assert "## Citations" in captured


def test_format_complex_response(capsys):
    """Test that the format method correctly handles a complex QueryResponse."""
    resp = QueryResponse(
        answer="This is a complex answer with multiple paragraphs.\n\nSecond paragraph.",
        citations=["Citation 1", "Citation 2 with [link](https://example.com)"],
        reasoning=["Reasoning step 1", "Reasoning step 2 with *emphasis*"],
        metrics={"tokens": 100, "time": 1.5, "sources": ["web", "knowledge_base"]},
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


def test_format_template_class():
    """Test the FormatTemplate class."""
    # Create a template
    template = FormatTemplate(
        name="test",
        description="Test template",
        template="Answer: ${answer}\nCitations: ${citations}",
    )

    # Create a response
    resp = QueryResponse(
        answer="Test answer",
        citations=["Citation 1", "Citation 2"],
        reasoning=["Reasoning"],
        metrics={"tokens": 100},
    )

    # Render the template
    result = template.render(resp)

    # Check the result
    assert "Answer: Test answer" in result
    assert "Citations: - Citation 1\n- Citation 2" in result


def test_format_template_missing_variable():
    """Test that FormatTemplate raises KeyError for missing variables."""
    # Create a template with a variable that doesn't exist
    template = FormatTemplate(
        name="test",
        description="Test template",
        template="Answer: ${answer}\nMissing: ${missing}",
    )

    # Create a response
    resp = QueryResponse(
        answer="Test answer",
        citations=["Citation"],
        reasoning=["Reasoning"],
        metrics={"tokens": 100},
    )

    # Verify that a KeyError is raised
    with pytest.raises(KeyError) as excinfo:
        template.render(resp)

    # Check the error message
    assert "missing" in str(excinfo.value)
    assert "Available variables" in str(excinfo.value)


def test_template_registry():
    """Test the TemplateRegistry class."""
    # Clear the registry
    TemplateRegistry._templates = {}

    # Create a template
    template = FormatTemplate(
        name="test_registry", description="Test template", template="Answer: ${answer}"
    )

    # Register the template
    TemplateRegistry.register(template)

    # Get the template
    retrieved = TemplateRegistry.get("test_registry")

    # Check the template
    assert retrieved.name == "test_registry"
    assert retrieved.description == "Test template"
    assert retrieved.template == "Answer: ${answer}"


def test_template_registry_default_templates():
    """Test that TemplateRegistry loads default templates."""
    # Clear the registry
    TemplateRegistry._templates = {}

    # Get a default template
    template = TemplateRegistry.get("markdown")

    # Check the template
    assert template.name == "markdown"
    assert "# Answer" in template.template
    assert "## Citations" in template.template


def test_template_registry_missing_template():
    """Test that TemplateRegistry raises KeyError for missing templates."""
    # Clear the registry
    TemplateRegistry._templates = {}

    # Verify that a KeyError is raised
    with pytest.raises(KeyError) as excinfo:
        TemplateRegistry.get("nonexistent")

    # Check the error message
    assert "not found" in str(excinfo.value)


def test_template_from_file():
    """Test loading a template from a file."""
    # Clear the registry
    TemplateRegistry._templates = {}

    # Create a temporary directory
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a template file
        template_dir = Path(tmpdir) / "templates"
        template_dir.mkdir()
        template_path = template_dir / "html.tpl"

        with open(template_path, "w") as f:
            f.write(
                "# HTML Template\n<html><body><h1>${answer}</h1><ul>${citations}</ul></body></html>"
            )

        # Mock the config to use the temporary directory
        with patch("autoresearch.output_format.ConfigLoader") as mock_config_loader:
            mock_config = MagicMock()
            mock_config.template_dir = str(template_dir)
            mock_config_loader.return_value.config = mock_config

            # Load the template
            template = TemplateRegistry.get("html")

            # Check the template
            assert template.name == "html"
            assert template.description == "HTML Template"
            assert "<html><body><h1>${answer}</h1>" in template.template


def test_template_from_config():
    """Test loading templates from configuration."""
    # Clear the registry
    TemplateRegistry._templates = {}

    # Create a mock config with templates
    with patch("autoresearch.output_format.ConfigLoader") as mock_config_loader:
        mock_config = MagicMock()
        mock_config.output_templates = {
            "html": {
                "description": "HTML Template",
                "template": "<html><body><h1>${answer}</h1><ul>${citations}</ul></body></html>",
            }
        }
        mock_config_loader.return_value.config = mock_config

        # Load templates from config
        TemplateRegistry.load_from_config()

        # Get the template
        template = TemplateRegistry.get("html")

        # Check the template
        assert template.name == "html"
        assert template.description == "HTML Template"
        assert "<html><body><h1>${answer}</h1>" in template.template


def test_format_with_custom_template(capsys):
    """Test formatting with a custom template."""
    # Clear the registry
    TemplateRegistry._templates = {}

    # Create a template
    template = FormatTemplate(
        name="custom",
        description="Custom template",
        template="ANSWER: ${answer}\nCITATIONS: ${citations}",
    )

    # Register the template
    TemplateRegistry.register(template)

    # Create a response
    resp = QueryResponse(
        answer="Test answer",
        citations=["Citation 1", "Citation 2"],
        reasoning=["Reasoning"],
        metrics={"tokens": 100},
    )

    # Format with the custom template
    OutputFormatter.format(resp, "template:custom")
    captured = capsys.readouterr().out

    # Check the result
    assert "ANSWER: Test answer" in captured
    assert "CITATIONS: - Citation 1\n- Citation 2" in captured


def test_format_with_missing_template(capsys):
    """Test formatting with a missing template falls back to markdown."""
    # Clear the registry
    TemplateRegistry._templates = {}

    # Create a response
    resp = QueryResponse(
        answer="Test answer",
        citations=["Citation"],
        reasoning=["Reasoning"],
        metrics={"tokens": 100},
    )

    # Format with a nonexistent template
    OutputFormatter.format(resp, "template:nonexistent")
    captured = capsys.readouterr().out

    # Check that it fell back to markdown
    assert "# Answer" in captured
    assert "## Citations" in captured
    assert "- Citation" in captured


def test_tldr_knowledge_graph_section_requires_summary() -> None:
    base_resp = QueryResponse(answer="a", citations=[], reasoning=[], metrics={})
    markdown_without = OutputFormatter.render(base_resp, "markdown", depth=OutputDepth.TLDR)
    assert "## Knowledge Graph" not in markdown_without

    summary = {
        "entity_count": 2,
        "relation_count": 1,
        "contradictions": [
            {"subject": "A", "predicate": "contradicts", "objects": ["B"]}
        ],
        "multi_hop_paths": [["A", "B", "C"]],
        "contradiction_score": 0.5,
    }
    kg_resp = QueryResponse(
        answer="a",
        citations=[],
        reasoning=[],
        metrics={
            "knowledge_graph": {
                "summary": summary,
                "exports": {"graphml": True, "graph_json": True},
            }
        },
    )
    markdown_with = OutputFormatter.render(kg_resp, "markdown", depth=OutputDepth.TLDR)
    assert "## Knowledge Graph" in markdown_with
    assert "Entities" in markdown_with
    assert "## Graph Exports" not in markdown_with


def test_trace_graph_exports_section_requires_summary() -> None:
    base_resp = QueryResponse(answer="trace", citations=[], reasoning=[], metrics={})
    trace_without = OutputFormatter.render(base_resp, "markdown", depth=OutputDepth.TRACE)
    assert "## Knowledge Graph" not in trace_without
    assert "## Graph Exports" not in trace_without

    summary = {
        "entity_count": 3,
        "relation_count": 2,
        "contradictions": [],
        "multi_hop_paths": [["X", "Y"]],
        "contradiction_score": 0.0,
    }
    kg_resp = QueryResponse(
        answer="trace",
        citations=[],
        reasoning=[],
        metrics={
            "knowledge_graph": {
                "summary": summary,
                "exports": {"graphml": True, "graph_json": True},
            }
        },
    )
    trace_with = OutputFormatter.render(kg_resp, "markdown", depth=OutputDepth.TRACE)
    assert "## Knowledge Graph" in trace_with
    assert "## Graph Exports" in trace_with
    assert "--output graphml" in trace_with
