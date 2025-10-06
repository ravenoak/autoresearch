"""Regression tests for storage claim audit provenance."""

from __future__ import annotations

from autoresearch import storage
from autoresearch.storage import ClaimAuditRecord


def test_record_claim_audit_persists_provenance_round_trip(tmp_path) -> None:
    """Claim audit provenance should survive storage round-trips."""

    db_path = tmp_path / "audits.duckdb"
    storage.teardown(remove_db=True)
    ctx = storage.initialize_storage(str(db_path))
    try:
        provenance = {
            "retrieval": {"base_query": "test", "events": []},
            "backoff": {"retry_count": 1},
            "evidence": {"best_source_id": "src-abc"},
        }
        record = ClaimAuditRecord.from_score(
            "claim-x",
            0.75,
            sources=[{"title": "Traceable", "snippet": "Claim x"}],
            provenance=provenance,
        )
        storage.StorageManager.record_claim_audit(record)

        round_tripped = storage.StorageManager.list_claim_audits("claim-x")
        assert len(round_tripped) == 1
        assert round_tripped[0].provenance == provenance
        assert round_tripped[0].provenance["backoff"]["retry_count"] == 1
        assert round_tripped[0].provenance["evidence"]["best_source_id"] == "src-abc"
    finally:
        storage.teardown(remove_db=True, context=ctx)
