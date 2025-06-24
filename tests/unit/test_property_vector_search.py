from unittest.mock import MagicMock
from hypothesis import given, strategies as st, settings, HealthCheck
import pytest


from autoresearch.storage import StorageManager


@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    st.lists(st.floats(allow_nan=False, allow_infinity=False), min_size=1, max_size=5),
    st.integers(min_value=1, max_value=5)
)
def test_vector_search_calls_backend(monkeypatch, query_embedding, k):
    backend = MagicMock()
    backend.vector_search.return_value = [{"node_id": "n", "embedding": [0.1]}]
    monkeypatch.setattr("autoresearch.storage._db_backend", backend, raising=False)
    monkeypatch.setattr(StorageManager, "_ensure_storage_initialized", lambda: None)
    monkeypatch.setattr(StorageManager, "has_vss", lambda: True)

    result = StorageManager.vector_search(query_embedding, k)
    backend.vector_search.assert_called_once_with(query_embedding, k)
    assert isinstance(result, list)


@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    st.one_of(st.none(), st.text(), st.integers(), st.lists(st.text())),
    st.integers(max_value=0)
)
def test_vector_search_invalid(monkeypatch, query_embedding, k):
    monkeypatch.setattr(StorageManager, "_ensure_storage_initialized", lambda: None)
    monkeypatch.setattr(StorageManager, "has_vss", lambda: True)
    with pytest.raises(Exception):
        StorageManager.vector_search(query_embedding, k)
