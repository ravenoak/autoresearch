from __future__ import annotations

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping, cast

import networkx as nx
from autoresearch.storage import (
    ClaimAuditStatus,
    StorageContext,
    StorageManager,
    StorageState,
)
from autoresearch.storage_backends import DuckDBStorageBackend, init_rdf_store


class _StubBackend(DuckDBStorageBackend):
    def __init__(self) -> None:
        super().__init__()
        self.persisted: list[dict[str, Any]] = []

    def persist_claim_audit(self, payload: Mapping[str, Any]) -> None:
        self.persisted.append(dict(payload))


def test_persist_claim_audit_payload_updates_backends(tmp_path: Path) -> None:
    graph: nx.DiGraph[Any] = nx.DiGraph()
    graph.add_node("claim-1")

    context = StorageContext(
        graph=graph,
        kg_graph=nx.MultiDiGraph[Any](),
        db_backend=_StubBackend(),
        rdf_store=init_rdf_store("memory", str(tmp_path / "rdf")),
    )
    state = StorageState(context=context)

    original_context = StorageManager.context
    original_state = StorageManager.state

    try:
        StorageManager.context = context
        StorageManager.state = state
        payload = {
            "claim_id": "claim-1",
            "status": ClaimAuditStatus.SUPPORTED.value,
            "sources": [{"id": "src-1"}],
        }

        record = StorageManager._persist_claim_audit_payload(payload)

        assert record.claim_id == "claim-1"
        assert context.db_backend is not None
        backend = cast(_StubBackend, context.db_backend)
        assert backend.persisted[0]["claim_id"] == "claim-1"
        assert context.graph is not None
        assert context.graph.nodes["claim-1"]["audit"]["status"] == "supported"
    finally:
        StorageManager.context = original_context
        StorageManager.state = original_state
