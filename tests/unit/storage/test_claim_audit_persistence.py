from __future__ import annotations

import networkx as nx
from autoresearch.storage import (
    ClaimAuditStatus,
    StorageContext,
    StorageManager,
    StorageState,
)
from autoresearch.storage_backends import init_rdf_store
from pathlib import Path


class _StubBackend:
    def __init__(self) -> None:
        self.persisted: list[dict[str, object]] = []

    def persist_claim_audit(self, payload: dict[str, object]) -> None:
        self.persisted.append(payload)


def test_persist_claim_audit_payload_updates_backends(tmp_path: Path) -> None:
    graph = nx.DiGraph()
    graph.add_node("claim-1")

    context = StorageContext(
        graph=graph,
        kg_graph=nx.MultiDiGraph(),
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
        assert context.db_backend.persisted[0]["claim_id"] == "claim-1"
        assert context.graph is not None
        assert context.graph.nodes["claim-1"]["audit"]["status"] == "supported"
    finally:
        StorageManager.context = original_context
        StorageManager.state = original_state
