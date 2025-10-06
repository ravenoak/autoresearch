from hypothesis import given, strategies as st
from autoresearch.output_format import FormatTemplate
from autoresearch.models import QueryResponse


@given(st.text(min_size=1), st.text(min_size=1))
def test_formattemplate_render(answer, citation):
    template = FormatTemplate(name="t", template="A:${answer};C:${citations}")
    resp = QueryResponse(answer=answer, citations=[citation], reasoning=[], metrics={})
    out = template.render(resp)
    assert answer in out and citation in out
