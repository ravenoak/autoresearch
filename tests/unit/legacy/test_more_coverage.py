# mypy: ignore-errors
from __future__ import annotations

from queue import Queue
from unittest.mock import MagicMock

import autoresearch.search as search_module
from autoresearch.monitor import (
    AUDIT_TELEMETRY_FIELDS,
    build_audit_telemetry,
    normalize_audit_payload,
)
from autoresearch.orchestration import execution as exec_mod
from autoresearch.orchestration.orchestration_utils import OrchestrationUtils
from autoresearch.output_format import FormatTemplate
from autoresearch.search import Search, close_http_session, get_http_session
from autoresearch.storage import StorageManager
from autoresearch.storage_backends import DuckDBStorageBackend

from tests.unit.typing_helpers import make_runtime_config, make_search_config


def test_log_sources(monkeypatch):
    mock_log = MagicMock()
    monkeypatch.setattr(exec_mod, "log", mock_log)
    OrchestrationUtils.log_sources("A", {"sources": [{"title": "T"}]})
    info_call = mock_log.info.call_args
    assert info_call is not None
    message = info_call.args[0]
    assert "provided 1 sources" in message
    assert info_call.kwargs.get("extra", {}).get("source_count") == 1


def test_log_sources_missing(monkeypatch):
    mock_log = MagicMock()
    monkeypatch.setattr(exec_mod, "log", mock_log)
    OrchestrationUtils.log_sources("A", {})
    warning_call = mock_log.warning.call_args
    assert warning_call is not None
    assert "provided no sources" in warning_call.args[0]


def test_persist_claims(monkeypatch):
    calls = []
    monkeypatch.setattr(StorageManager, "persist_claim", lambda c: calls.append(c["id"]))
    result = {"claims": [{"id": "c1"}, {"id": "c2"}]}
    OrchestrationUtils.persist_claims("A", result, StorageManager)
    assert calls == ["c1", "c2"]


def test_persist_claims_invalid(monkeypatch):
    monkeypatch.setattr(StorageManager, "persist_claim", lambda c: None)
    mock_log = MagicMock()
    monkeypatch.setattr(exec_mod, "log", mock_log)
    result = {"claims": ["bad", {"foo": 1}]}
    OrchestrationUtils.persist_claims("A", result, StorageManager)
    warnings = [call.args[0] for call in mock_log.warning.call_args_list]
    assert any("Skipping invalid claim format" in msg for msg in warnings)


def test_ndcg_perfect():
    rel = [3, 2, 1]
    assert Search._ndcg(rel) == Search._ndcg(sorted(rel, reverse=True))


def test_http_session_cycle(monkeypatch):
    cfg = make_runtime_config(search=make_search_config(http_pool_size=1))
    monkeypatch.setattr("autoresearch.search.core.get_config", lambda: cfg)
    close_http_session()
    s1 = get_http_session()
    s2 = get_http_session()
    assert s1 is s2
    close_http_session()
    assert search_module._http_session is None


def test_connection_context_manager_pool():
    backend = DuckDBStorageBackend()
    conn = MagicMock()
    backend._pool = Queue()
    backend._pool.put(conn)
    with backend.connection() as c:
        assert c is conn
    assert not backend._pool.empty()


def test_connection_context_manager_single():
    backend = DuckDBStorageBackend()
    conn = MagicMock()
    backend._conn = conn
    with backend.connection() as c:
        assert c is conn


def test_formattemplate_metrics():
    tpl = FormatTemplate(name="m", template="Tokens: ${metric_tokens}")
    resp = type(
        "R",
        (),
        {
            "answer": "a",
            "citations": [],
            "reasoning": [],
            "metrics": {"tokens": 5},
            "claim_audits": [],
            "notes": {},
        },
    )()
    assert tpl.render(resp) == "Tokens: 5"


def test_normalize_audit_payload_includes_expected_fields() -> None:
    payload = normalize_audit_payload(
        {
            "audit_id": 42,
            "claim_id": 123,
            "status": "verified",
            "entailment_score": "0.75",
            "entailment_variance": "0.1",
            "instability_flag": "true",
            "sample_size": "5",
            "sources": [{"id": "s1"}, "skip"],
            "provenance": {"retrieval": ["doc"]},
            "notes": 99,
            "created_at": "1700000000.5",
        }
    )
    assert set(payload) == set(AUDIT_TELEMETRY_FIELDS)
    assert payload["claim_id"] == "123"
    assert payload["status"] == "verified"
    assert payload["entailment_score"] == 0.75
    assert payload["entailment_variance"] == 0.1
    assert payload["instability_flag"] is True
    assert payload["sample_size"] == 5
    assert payload["sources"] == [{"id": "s1"}]
    assert payload["provenance"] == {"retrieval": ["doc"]}
    assert payload["notes"] == "99"
    assert isinstance(payload["created_at"], float)


def test_build_audit_telemetry_summarises_audits() -> None:
    audits = [
        {
            "audit_id": "a1",
            "claim_id": "c1",
            "status": "verified",
            "instability_flag": False,
            "sources": [],
            "provenance": {},
        },
        {
            "audit_id": "a2",
            "claim_id": "c2",
            "status": "needs_review",
            "instability_flag": True,
            "sources": [],
            "provenance": {},
        },
        "not-a-mapping",
    ]
    snapshot = build_audit_telemetry(audits)
    assert snapshot["audit_records"] == 2
    assert snapshot["flagged_records"] == 1
    assert snapshot["status_counts"] == {"verified": 1, "needs_review": 1}
    assert snapshot["claim_ids"] == ["c1", "c2"]
    assert all(set(entry) == set(AUDIT_TELEMETRY_FIELDS) for entry in snapshot["audits"])
