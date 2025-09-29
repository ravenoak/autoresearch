from __future__ import annotations

from autoresearch.config import ConfigModel, StorageConfig, temporary_config
from autoresearch.storage import ClaimAuditStatus, StorageContext, StorageManager, StorageState
from unittest.mock import patch


def test_storage_persistence_and_audit_flow(tmp_path) -> None:
    db_path = tmp_path / "kg.duckdb"
    rdf_path = tmp_path / "rdf"
    config = ConfigModel(
        storage=StorageConfig(
            duckdb_path=str(db_path),
            rdf_backend="memory",
            rdf_path=str(rdf_path),
            vector_extension=False,
        )
    )

    context = StorageContext()
    state = StorageState(context=context)
    original_context = StorageManager.context
    original_state = StorageManager.state

    try:
        with temporary_config(config):
            StorageManager.setup(str(db_path), context=context, state=state)
            claim = {
                "id": "typed-claim",
                "type": "claim",
                "content": "Typed persistence check",
                "attributes": {"topic": "typing"},
                "audit": {
                    "claim_id": "typed-claim",
                    "status": ClaimAuditStatus.SUPPORTED.value,
                    "sources": [{"id": "src-1"}],
                },
            }
            with patch("autoresearch.storage.run_ontology_reasoner", autospec=True) as mock_reasoner:
                StorageManager.persist_claim(claim)
                mock_reasoner.assert_called()

            graph = StorageManager.context.graph
            assert graph is not None and graph.has_node("typed-claim")
            audit_payload = graph.nodes["typed-claim"]["audit"]
            assert isinstance(audit_payload, dict)
            assert audit_payload["status"] == "supported"

            audits = StorageManager.list_claim_audits("typed-claim")
            assert audits and audits[0].claim_id == "typed-claim"
            assert audits[0].status is ClaimAuditStatus.SUPPORTED

            with patch("autoresearch.storage.run_ontology_reasoner", autospec=True):
                StorageManager.clear_all()
            assert StorageManager.context.graph is not None
            assert len(StorageManager.context.graph.nodes) == 0
    finally:
        StorageManager.teardown(remove_db=True, context=context, state=state)
        StorageManager.context = original_context
        StorageManager.state = original_state
