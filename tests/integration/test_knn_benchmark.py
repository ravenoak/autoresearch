import os
import time
import numpy as np
import pytest
from autoresearch.storage import StorageManager
import duckdb
from autoresearch.extensions import VSSExtensionLoader
from autoresearch.config import ConfigModel, StorageConfig, ConfigLoader

try:
    _tmp_conn = duckdb.connect(database=":memory:")
    VSS_AVAILABLE = VSSExtensionLoader.verify_extension(_tmp_conn, verbose=False)
    _tmp_conn.close()
except Exception:
    VSS_AVAILABLE = False

pytestmark = [
    pytest.mark.slow,
    pytest.mark.requires_vss,
    pytest.mark.skipif(not VSS_AVAILABLE, reason="VSS extension not available"),
]


def test_knn_latency_benchmark(tmp_path, monkeypatch):
    cfg = ConfigModel(
        storage=StorageConfig(
            vector_extension=True,
            duckdb_path=str(tmp_path / "bench.duckdb"),
        )
    )
    monkeypatch.setattr(ConfigLoader, "load_config", lambda self: cfg)
    ConfigLoader()._config = None

    StorageManager.clear_all()
    conn = StorageManager.get_duckdb_conn()

    dim = 384
    n = int(os.environ.get("KNN_BENCHMARK_N", "1000"))
    nodes = [(f"n{i}", "", "", 0.0) for i in range(n)]
    vectors = [(f"n{i}", np.random.rand(dim).astype(float).tolist()) for i in range(n)]

    conn.executemany(
        "INSERT INTO nodes VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)", nodes
    )
    conn.executemany("INSERT INTO embeddings VALUES (?, ?)", vectors)

    StorageManager.refresh_vector_index()

    query = vectors[0][1]
    start = time.perf_counter()
    StorageManager.vector_search(query, k=5)
    latency = time.perf_counter() - start
    assert latency < 0.15, f"Latency {latency:.3f}s exceeds 150ms"
