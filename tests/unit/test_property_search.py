from hypothesis import given, strategies as st
from autoresearch.search import Search
from typing import Any


@given(st.text(min_size=1))
def test_generate_queries_variants(query: Any) -> None:
    results = Search.generate_queries(query)
    cleaned = query.strip()
    if len(cleaned.split()) > 1:
        assert results == [cleaned, f"{cleaned} examples", f"What is {cleaned}?"]
    else:
        assert results == [cleaned, f"What is {cleaned}?"]
    assert Search.generate_queries(query) == results


@given(st.text(min_size=1))
def test_generate_queries_embeddings(query: Any) -> None:
    results = Search.generate_queries(query, return_embeddings=True)
    cleaned = query.strip()
    expected = [float(ord(c)) for c in cleaned][:10]
    assert results == expected
