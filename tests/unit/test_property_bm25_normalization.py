import pytest
from hypothesis import given, strategies as st

from autoresearch.search import Search

pytestmark = pytest.mark.requires_nlp


@given(query=st.text(min_size=1), doc=st.text(min_size=1))
@pytest.mark.xfail(reason="BM25 scoring may produce values outside [0,1]", strict=False)
def test_bm25_scores_normalized(query: str, doc: str) -> None:
    score = Search.calculate_bm25_scores(query, [{"title": doc}])[0]
    assert 0.0 <= score <= 1.0
