"""Property tests for output formatter.

See `docs/specification.md` and
`docs/algorithms/output_format.md`.
"""

import json
from hypothesis import given, strategies as st, settings, HealthCheck
from autoresearch.output_format import OutputFormatter
from autoresearch.models import QueryResponse


@settings(suppress_health_check=[HealthCheck.too_slow, HealthCheck.function_scoped_fixture])
@given(
    answer=st.text(min_size=1, max_size=20),
    citations=st.lists(st.text(min_size=1, max_size=15), max_size=3),
    reasoning=st.lists(st.text(min_size=1, max_size=15), max_size=3),
)
def test_output_formatter_json_markdown(answer, citations, reasoning, capsys):
    resp = QueryResponse(answer=answer, citations=citations, reasoning=reasoning, metrics={})
    OutputFormatter.format(resp, "json")
    parsed = json.loads(capsys.readouterr().out)
    assert parsed["answer"] == answer
    assert parsed["citations"] == citations

    OutputFormatter.format(resp, "markdown")
    md = capsys.readouterr().out
    assert answer in md
    for c in citations:
        assert c in md
