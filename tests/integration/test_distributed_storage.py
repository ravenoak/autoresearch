import os
import ray
import pytest
from autoresearch.config import ConfigModel, DistributedConfig, StorageConfig
from autoresearch.distributed import start_storage_coordinator
from autoresearch.storage import StorageManager

pytestmark = pytest.mark.slow


def test_distributed_storage(tmp_path):
    cfg = ConfigModel(
        distributed=True,
        distributed_config=DistributedConfig(enabled=True, num_cpus=2, message_broker="memory"),
        storage=StorageConfig(duckdb_path=str(tmp_path / "kg.duckdb")),
    )

    coordinator, broker = start_storage_coordinator(cfg)
    ray.init(num_cpus=2, ignore_reinit_error=True, configure_logging=False)

    @ray.remote
    def persist(claim, q):
        q.put({"action": "persist_claim", "claim": claim})
        return os.getpid()

    claims = [
        {"id": "c1", "type": "fact", "content": "a"},
        {"id": "c2", "type": "fact", "content": "b"},
    ]
    pids = ray.get([persist.remote(c, broker.queue) for c in claims])
    assert len(set(pids)) == len(claims)

    broker.publish({"action": "stop"})
    coordinator.join()
    broker.shutdown()
    os.environ["RAY_IGNORE_UNHANDLED_ERRORS"] = "1"
    ray.shutdown()

    StorageManager.setup(str(tmp_path / "kg.duckdb"))
    conn = StorageManager.get_duckdb_conn()
    rows = conn.execute("SELECT id FROM nodes ORDER BY id").fetchall()
    assert [r[0] for r in rows] == ["c1", "c2"]
