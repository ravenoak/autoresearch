import pytest

from tests.optional_imports import import_or_skip

from autoresearch.data_analysis import metrics_dataframe
from autoresearch.storage_backends import KuzuStorageBackend

pytestmark = pytest.mark.requires_analysis

import_or_skip("polars")


def test_kuzu_backend_roundtrip(tmp_path):
    path = tmp_path / "test_kuzu"
    backend = KuzuStorageBackend()
    backend.setup(str(path))
    claim = {"id": "1", "content": "hello"}
    backend.persist_claim(claim)
    result = backend.get_claim("1")
    assert result["content"] == "hello"


# Spec: docs/specs/data-analysis.md#polars-enabled
def test_metrics_dataframe():
    metrics = {"agent_timings": {"A": [1.0, 2.0], "B": [3.0]}}
    df = metrics_dataframe(metrics, polars_enabled=True)
    assert df.shape[0] == 2
    assert "avg_time" in df.columns
