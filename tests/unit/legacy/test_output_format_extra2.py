"""Template fallback tests referencing specification.

See `docs/specification.md` and
`docs/algorithms/output_format.md`.
"""

import logging

from autoresearch.output_format import FormatTemplate, OutputFormatter, TemplateRegistry
from autoresearch.models import QueryResponse

logging.getLogger("autoresearch.output_format").setLevel(logging.CRITICAL)


def test_metric_variable_rendering():
    template = FormatTemplate(name="metrics", template="Tokens: ${metric_tokens}")
    resp = QueryResponse(answer="a", citations=[], reasoning=[], metrics={"tokens": 5})
    assert template.render(resp) == "Tokens: 5"


def test_format_missing_variable_fallback(capsys):
    TemplateRegistry._templates = {}
    TemplateRegistry.register(FormatTemplate(name="bad", template="${missing}"))
    resp = QueryResponse(answer="a", citations=[], reasoning=[], metrics={})
    OutputFormatter.format(resp, "template:bad")
    out = capsys.readouterr().out
    assert "# Answer" in out  # fell back to markdown
