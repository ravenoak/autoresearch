# mypy: ignore-errors
from __future__ import annotations

import os
from pathlib import Path
from typing import cast

import pytest
import ray

from autoresearch.config.models import ConfigModel, DistributedConfig, StorageConfig
from autoresearch.distributed import (
    BrokerType,
    StorageCoordinator,
    start_storage_coordinator,
)
from autoresearch.distributed.broker import (
    PersistClaimMessage,
    STOP_MESSAGE,
    StorageBrokerQueueProtocol,
)
from autoresearch.storage import (
    StorageContext,
    StorageManager,
    StorageState,
)
from autoresearch.storage_typing import JSONDict

pytestmark = pytest.mark.slow


def test_distributed_storage(tmp_path: Path) -> None:
    db_path: Path = tmp_path / "kg.duckdb"
    cfg: ConfigModel = ConfigModel(
        distributed=True,
        distributed_config=DistributedConfig(
            enabled=True, num_cpus=2, message_broker="memory"
        ),
        storage=StorageConfig(duckdb_path=str(db_path)),
    )

    coordinator: StorageCoordinator
    broker_instance: BrokerType
    coordinator, broker_instance = start_storage_coordinator(cfg)
    ray.init(num_cpus=2, ignore_reinit_error=True, configure_logging=False)

    @ray.remote
    def persist(claim: JSONDict, q: StorageBrokerQueueProtocol) -> int:
        message: PersistClaimMessage = {
            "action": "persist_claim",
            "claim": claim,
            "partial_update": False,
        }
        q.put(message)
        return os.getpid()

    claims: list[JSONDict] = [
        {"id": "c1", "type": "fact", "content": "a"},
        {"id": "c2", "type": "fact", "content": "b"},
    ]
    pids = cast(list[int], ray.get([persist.remote(c, broker_instance.queue) for c in claims]))
    assert len({pid for pid in pids}) == len(claims)

    broker_instance.publish(STOP_MESSAGE)
    coordinator.join()
    broker_instance.shutdown()
    os.environ["RAY_IGNORE_UNHANDLED_ERRORS"] = "1"
    ray.shutdown()

    context: StorageContext = StorageContext()
    state: StorageState = StorageState(context=context)
    StorageManager.setup(str(db_path), context=context, state=state)
    try:
        conn = StorageManager.get_duckdb_conn()
        rows: list[tuple[str]] = conn.execute(
            "SELECT id FROM nodes ORDER BY id"
        ).fetchall()
    finally:
        StorageManager.teardown(remove_db=True, context=context, state=state)
        StorageManager.state = StorageState()
        StorageManager.context = StorageContext()

    assert [row[0] for row in rows] == ["c1", "c2"]
