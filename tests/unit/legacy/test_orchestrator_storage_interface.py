"""Tests for orchestrator static methods interacting with storage."""

from types import SimpleNamespace
from unittest.mock import patch

from autoresearch.orchestration.orchestrator import Orchestrator
from autoresearch.storage import StorageManager


def test_infer_relations_calls_storage():
    """Orchestrator.infer_relations should delegate to StorageManager."""
    with patch.object(StorageManager, "infer_relations") as mock_infer:
        Orchestrator.infer_relations()
        mock_infer.assert_called_once()


def test_query_ontology_calls_storage():
    """Orchestrator.query_ontology should delegate to StorageManager."""
    sentinel = object()
    with patch.object(StorageManager, "query_ontology", return_value=sentinel) as mock_query:
        result = Orchestrator.query_ontology("SELECT ?s WHERE { ?s ?p ?o }")
        mock_query.assert_called_once_with("SELECT ?s WHERE { ?s ?p ?o }")
        assert result is sentinel


def test_run_parallel_query_delegates(monkeypatch):
    """run_parallel_query should invoke parallel.execute_parallel_query."""
    called = {}

    def fake_execute(query, config, groups, timeout):
        called["args"] = (query, config, groups, timeout)
        return "resp"

    monkeypatch.setattr(
        "autoresearch.orchestration.parallel.execute_parallel_query",
        fake_execute,
    )
    cfg = SimpleNamespace()
    resp = Orchestrator.run_parallel_query("q", cfg, [["a"]], timeout=1)
    assert called["args"] == ("q", cfg, [["a"]], 1)
    assert resp == "resp"
