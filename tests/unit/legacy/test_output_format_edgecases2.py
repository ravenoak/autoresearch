"""Graph output tests.

Spec reference: `docs/specification.md` and
`docs/algorithms/output_format.md`.
"""

from autoresearch.output_format import OutputFormatter
from autoresearch.models import QueryResponse


def test_graph_format(capsys):
    resp = QueryResponse(answer="a", citations=["c"], reasoning=[], metrics={})
    OutputFormatter.format(resp, "graph")
    out = capsys.readouterr().out
    assert "Knowledge Graph" in out
