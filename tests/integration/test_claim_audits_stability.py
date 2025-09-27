"""Integration tests for claim audit stability metadata."""

import pytest

from autoresearch.storage import ClaimAuditRecord
from autoresearch.storage_backends import DuckDBStorageBackend


def test_duckdb_persists_stability_metadata() -> None:
    """Persisting and retrieving claim audits should round-trip stability fields."""

    backend = DuckDBStorageBackend()
    backend.setup(db_path=":memory:", skip_migrations=False)
    try:
        record = ClaimAuditRecord.from_score(
            "claim-123",
            0.8,
            variance=0.02,
            instability=False,
            sample_size=5,
        )
        backend.persist_claim_audit(record.to_payload())

        audits = backend.list_claim_audits("claim-123")
        assert audits, "Expected persisted audit to be retrievable"
        stored = audits[0]
        assert stored["entailment_variance"] == pytest.approx(0.02)
        assert stored["instability_flag"] is False
        assert stored["sample_size"] == 5
    finally:
        backend.close()
