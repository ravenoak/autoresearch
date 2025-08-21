import pytest
from hypothesis import given, strategies as st

from autoresearch.search import Search

pytestmark = pytest.mark.requires_nlp


@given(query=st.text(min_size=1), doc=st.text(min_size=1))
def test_bm25_scores_normalized(query: str, doc: str) -> None:
    score = Search.calculate_bm25_scores(query, [{"title": doc}])[0]
    assert 0.0 <= score <= 1.0
