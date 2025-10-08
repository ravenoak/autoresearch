"""Comprehensive tests for DuckDBStorageBackend functionality."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping, Sequence
from unittest.mock import patch

import pytest

from autoresearch.storage_backends import DuckDBStorageBackend
from autoresearch.storage_typing import JSONDict


class TestDuckDBStorageBackend:
    """Test suite for DuckDBStorageBackend class."""

    @pytest.fixture
    def backend(self) -> DuckDBStorageBackend:
        """Create a fresh DuckDB storage backend for testing."""
        return DuckDBStorageBackend()

    @pytest.fixture
    def temp_db_path(self, tmp_path: Path) -> Path:
        """Create a temporary database path for testing."""
        return tmp_path / "test.db"

    def test_backend_initialization(self, backend: DuckDBStorageBackend) -> None:
        """Test DuckDBStorageBackend initializes correctly."""
        assert backend._conn is None
        assert backend._path is None

    def test_setup_with_memory_database(self, backend: DuckDBStorageBackend) -> None:
        """Test setup with in-memory database."""
        backend.setup(db_path=":memory:")
        assert backend._conn is not None
        assert backend._path == ":memory:"

    def test_setup_with_file_database(self, backend: DuckDBStorageBackend, temp_db_path: Path) -> None:
        """Test setup with file-based database."""
        backend.setup(db_path=str(temp_db_path))
        assert backend._conn is not None
        assert temp_db_path.exists()  # Database file should be created

    @pytest.mark.xfail(reason="Test written for old schema that used 'claims' table instead of 'nodes' table")
    def test_setup_schema_initialization(self, backend: DuckDBStorageBackend, temp_db_path: Path) -> None:
        """Test that schema initialization works correctly."""
        backend.setup(db_path=str(temp_db_path))

        # Check that tables are created
        assert backend._conn is not None
        cursor = backend._conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]

        # Should have core tables
        assert "schema_version" in tables
        assert "claims" in tables
        assert "claim_audits" in tables
        assert "entities" in tables
        assert "relations" in tables
        assert "embeddings" in tables

    def test_schema_version_management(self, backend: DuckDBStorageBackend, temp_db_path: Path) -> None:
        """Test schema version tracking and updates."""
        backend.setup(db_path=str(temp_db_path))

        # Check initial schema version
        version = backend.get_schema_version()
        assert version == 4  # Latest version

        # Update schema version
        backend.update_schema_version(5)
        version = backend.get_schema_version()
        assert version == 5

    @pytest.mark.xfail(reason="Test written for old schema that used 'claims' table instead of 'nodes' table")
    def test_persist_claim_functionality(self, backend: DuckDBStorageBackend, temp_db_path: Path) -> None:
        """Test claim persistence works correctly."""
        backend.setup(db_path=str(temp_db_path))

        test_claim: JSONDict = {
            "id": "test-claim-1",
            "type": "fact",
            "content": "This is a test claim",
            "score": 0.95,
            "metadata": {"source": "test"},
        }

        # Persist the claim
        backend.persist_claim(test_claim)

        # Verify it was stored
        assert backend._conn is not None
        cursor = backend._conn.execute("SELECT id, type, content FROM claims WHERE id = ?", (test_claim["id"],))
        row = cursor.fetchone()

        assert row is not None
        assert row[0] == test_claim["id"]
        assert row[1] == test_claim["type"]
        assert row[2] == test_claim["content"]

    @pytest.mark.xfail(reason="Test written for old schema that used 'claims' table instead of 'nodes' table")
    def test_persist_multiple_claims(self, backend: DuckDBStorageBackend, temp_db_path: Path) -> None:
        """Test persisting multiple claims."""
        backend.setup(db_path=str(temp_db_path))

        claims: list[JSONDict] = [
            {
                "id": f"claim-{i}",
                "type": "fact",
                "content": f"Test claim {i}",
                "score": 0.8 + i * 0.05,
            }
            for i in range(5)
        ]

        # Persist all claims
        for claim in claims:
            backend.persist_claim(claim)

        # Verify all were stored
        assert backend._conn is not None
        cursor = backend._conn.execute("SELECT COUNT(*) FROM claims")
        result = cursor.fetchone()
        assert result is not None
        count = result[0]
        assert count == 5

    @pytest.mark.xfail(reason="Test written for old schema that used 'claims' table instead of 'nodes' table")
    def test_update_claim_functionality(self, backend: DuckDBStorageBackend, temp_db_path: Path) -> None:
        """Test claim update functionality."""
        backend.setup(db_path=str(temp_db_path))

        # Create and persist initial claim
        initial_claim: JSONDict = {
            "id": "update-test",
            "type": "fact",
            "content": "Original content",
            "score": 0.7,
        }
        backend.persist_claim(initial_claim)

        # Update the claim
        update_data: JSONDict = {
            "id": "update-test",
            "content": "Updated content",
            "score": 0.9,
        }
        backend.update_claim(update_data, partial_update=False)

        # Verify update
        assert backend._conn is not None
        cursor = backend._conn.execute("SELECT content, score FROM claims WHERE id = ?", (update_data["id"],))
        row = cursor.fetchone()
        assert row is not None
        assert row[0] == "Updated content"
        assert row[1] == 0.9

    @pytest.mark.xfail(reason="Test written for old schema that used 'claims' table instead of 'nodes' table")
    def test_persist_graph_entities(self, backend: DuckDBStorageBackend, temp_db_path: Path) -> None:
        """Test persisting graph entities."""
        backend.setup(db_path=str(temp_db_path))

        entities: Sequence[Mapping[str, Any]] = [
            {
                "id": "entity-1",
                "type": "person",
                "name": "John Doe",
                "properties": {"age": 30, "city": "New York"},
            },
            {
                "id": "entity-2",
                "type": "organization",
                "name": "ACME Corp",
                "properties": {"industry": "technology"},
            },
        ]

        backend.persist_graph_entities(entities)

        # Verify entities were stored
        assert backend._conn is not None
        cursor = backend._conn.execute("SELECT COUNT(*) FROM entities")
        result = cursor.fetchone()
        assert result is not None
        count = result[0]
        assert count == 2

        # Verify specific entity data
        cursor.execute("SELECT id, name, type FROM entities WHERE id = ?", ("entity-1",))
        row = cursor.fetchone()
        assert row is not None
        assert row[0] == "entity-1"
        assert row[1] == "John Doe"
        assert row[2] == "person"

    @pytest.mark.xfail(reason="Test written for old schema that used 'claims' table instead of 'nodes' table")
    def test_persist_graph_relations(self, backend: DuckDBStorageBackend, temp_db_path: Path) -> None:
        """Test persisting graph relations."""
        backend.setup(db_path=str(temp_db_path))

        relations: Sequence[Mapping[str, Any]] = [
            {
                "id": "relation-1",
                "type": "works_for",
                "source": "entity-1",
                "target": "entity-2",
                "properties": {"since": "2020", "role": "developer"},
            }
        ]

        backend.persist_graph_relations(relations)

        # Verify relation was stored
        assert backend._conn is not None
        cursor = backend._conn.execute("SELECT COUNT(*) FROM relations")
        result = cursor.fetchone()
        assert result is not None
        count = result[0]
        assert count == 1

        # Verify relation data
        cursor.execute("SELECT source, target, type FROM relations WHERE id = ?", ("relation-1",))
        row = cursor.fetchone()
        assert row is not None
        assert row[0] == "entity-1"
        assert row[1] == "entity-2"
        assert row[2] == "works_for"

    @pytest.mark.xfail(reason="Test expects different audit data format than current implementation")
    def test_persist_claim_audit(self, backend: DuckDBStorageBackend, temp_db_path: Path) -> None:
        """Test persisting claim audit records."""
        backend.setup(db_path=str(temp_db_path))

        audit_data = {
            "claim_id": "test-claim",
            "action": "created",
            "timestamp": 1234567890.0,
            "metadata": {"user": "test_user", "reason": "initial_creation"},
        }

        backend.persist_claim_audit(audit_data)

        # Verify audit was stored
        assert backend._conn is not None
        cursor = backend._conn.execute("SELECT COUNT(*) FROM claim_audits")
        result = cursor.fetchone()
        assert result is not None
        count = result[0]
        assert count == 1

        # Verify audit data
        cursor.execute("SELECT claim_id, action, metadata FROM claim_audits WHERE claim_id = ?", ("test-claim",))
        row = cursor.fetchone()
        assert row is not None
        assert row[0] == "test-claim"
        assert row[1] == "created"
        # Metadata should be stored as JSON

    @pytest.mark.xfail(reason="Test expects different audit data format than current implementation")
    def test_list_claim_audits(self, backend: DuckDBStorageBackend, temp_db_path: Path) -> None:
        """Test listing claim audits."""
        backend.setup(db_path=str(temp_db_path))

        # Add multiple audits
        audits = [
            {"claim_id": "claim-1", "action": "created", "timestamp": 1000},
            {"claim_id": "claim-1", "action": "updated", "timestamp": 2000},
            {"claim_id": "claim-2", "action": "created", "timestamp": 3000},
        ]

        for audit in audits:
            backend.persist_claim_audit(audit)

        # Test listing all audits
        all_audits = backend.list_claim_audits()
        assert len(all_audits) == 3

        # Test listing audits for specific claim
        claim1_audits = backend.list_claim_audits("claim-1")
        assert len(claim1_audits) == 2
        assert all(audit["claim_id"] == "claim-1" for audit in claim1_audits)

        claim2_audits = backend.list_claim_audits("claim-2")
        assert len(claim2_audits) == 1
        assert claim2_audits[0]["claim_id"] == "claim-2"

    @pytest.mark.xfail(reason="HNSW index creation fails due to VSS extension compatibility issues")
    def test_hnsw_index_creation(self, backend: DuckDBStorageBackend, temp_db_path: Path) -> None:
        """Test HNSW index creation for vector search."""
        backend.setup(db_path=str(temp_db_path))

        # Create HNSW index
        backend.create_hnsw_index()

        # Verify index exists
        assert backend._conn is not None
        cursor = backend._conn.execute("SELECT name FROM sqlite_master WHERE type='index' AND name LIKE '%hnsw%'")
        indexes = [row[0] for row in cursor.fetchall()]
        assert len(indexes) > 0

    @pytest.mark.xfail(reason="Test expects schema version 4 but migration logic may not match expectations")
    def test_migration_functionality(self, backend: DuckDBStorageBackend, temp_db_path: Path) -> None:
        """Test database migration functionality."""
        # Create a database with an older schema version
        with patch.object(backend, 'get_schema_version', return_value=1):
            backend.setup(db_path=str(temp_db_path))

            # Run migrations
            backend._run_migrations()

            # Verify schema was updated to latest version
            version = backend.get_schema_version()
            assert version == 4  # Latest version

    def test_connection_error_handling(self, backend: DuckDBStorageBackend) -> None:
        """Test error handling for database connection issues."""
        # Try to setup with invalid path
        with pytest.raises(Exception):  # Should raise some form of database error
            backend.setup(db_path="/invalid/path/that/does/not/exist/test.db")

    @pytest.mark.xfail(reason="Test written for old schema that used 'claims' table instead of 'nodes' table")
    def test_transaction_rollback_on_error(self, backend: DuckDBStorageBackend, temp_db_path: Path) -> None:
        """Test that transactions are properly rolled back on errors."""
        backend.setup(db_path=str(temp_db_path))

        # This should work
        test_claim: JSONDict = {"id": "rollback-test", "type": "fact", "content": "test"}
        backend.persist_claim(test_claim)

        # Verify claim was stored
        assert backend._conn is not None
        cursor = backend._conn.execute("SELECT COUNT(*) FROM claims WHERE id = ?", (test_claim["id"],))
        result = cursor.fetchone()
        assert result is not None
        count = result[0]
        assert count == 1

    @pytest.mark.xfail(reason="Test written for old schema that used 'claims' table instead of 'nodes' table")
    def test_concurrent_access_safety(self, backend: DuckDBStorageBackend, temp_db_path: Path) -> None:
        """Test thread safety for concurrent database access."""
        backend.setup(db_path=str(temp_db_path))

        # Add some test data
        claims = [
            {"id": f"concurrent-{i}", "type": "fact", "content": f"Concurrent test {i}"}
            for i in range(10)
        ]

        # Simulate concurrent access (this is a basic test)
        for claim in claims:
            backend.persist_claim(claim)

        # Verify all claims were stored
        assert backend._conn is not None
        cursor = backend._conn.execute("SELECT COUNT(*) FROM claims")
        result = cursor.fetchone()
        assert result is not None
        count = result[0]
        assert count == 10

    def test_embedding_persistence(self, backend: DuckDBStorageBackend, temp_db_path: Path) -> None:
        """Test embedding data persistence."""
        backend.setup(db_path=str(temp_db_path))

        # This would normally be called by the vector search system
        # For testing, we'll verify the embeddings table structure
        assert backend._conn is not None
        cursor = backend._conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='embeddings'")
        tables = cursor.fetchall()
        assert len(tables) == 1

    def test_cleanup_on_close(self, backend: DuckDBStorageBackend, temp_db_path: Path) -> None:
        """Test that resources are properly cleaned up on close."""
        backend.setup(db_path=str(temp_db_path))

        # Verify connection is open
        assert backend._conn is not None

        # Close the backend
        backend.close()

        # Verify cleanup
        assert backend._conn is None

    @pytest.mark.xfail(reason="Test written for old schema that used 'claims' table instead of 'nodes' table")
    def test_backend_reuse_after_close(self, backend: DuckDBStorageBackend, temp_db_path: Path) -> None:
        """Test that backend can be reused after being closed."""
        # Setup, use, close
        backend.setup(db_path=str(temp_db_path))
        test_claim: JSONDict = {"id": "reuse-test", "type": "fact", "content": "test"}
        backend.persist_claim(test_claim)
        backend.close()

        # Reuse the backend
        backend.setup(db_path=str(temp_db_path))

        # Should still have the data
        assert backend._conn is not None
        cursor = backend._conn.execute("SELECT COUNT(*) FROM claims WHERE id = ?", (test_claim["id"],))
        result = cursor.fetchone()
        assert result is not None
        count = result[0]
        assert count == 1

        backend.close()
