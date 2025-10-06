# mypy: ignore-errors
"""Edge case tests for output formatting.

References `docs/specification.md` and
`docs/algorithms/output_format.md`.
"""

from autoresearch.output_format import OutputFormatter, TemplateRegistry
from autoresearch.models import QueryResponse


def test_template_fallback_to_markdown(capsys, monkeypatch):
    def raise_key(name):
        raise KeyError(name)

    monkeypatch.setattr(TemplateRegistry, "get", raise_key)
    resp = QueryResponse(answer="a", citations=[], reasoning=[], metrics={})
    OutputFormatter.format(resp, "template:missing")
    out = capsys.readouterr().out
    assert "# Answer" in out
