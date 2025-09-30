"""Graph output tests.

Spec reference: `docs/specification.md` and
`docs/algorithms/output_format.md`.
"""

from autoresearch.output_format import OutputFormatter
from autoresearch.models import QueryResponse
import pytest


def test_graph_format(capsys: pytest.CaptureFixture[str]) -> None:
    resp = QueryResponse(answer="a", citations=["c"], reasoning=[], metrics={})
    OutputFormatter.format(resp, "graph")
    out = capsys.readouterr().out
    assert "Knowledge Graph" in out
