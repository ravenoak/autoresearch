from __future__ import annotations

from typing import Any, ClassVar

import pytest
from fastapi.testclient import TestClient
from typer.testing import CliRunner

from autoresearch.api import app as api_app
from autoresearch.config.models import ConfigModel
from autoresearch.errors import StorageError
from autoresearch.llm import DummyAdapter
from autoresearch.main import app as cli_app
from autoresearch.models import QueryResponse
from autoresearch.orchestration.orchestrator import Orchestrator
from autoresearch.orchestration.state import QueryState
from autoresearch.orchestration.types import CallbackMap
from tests.integration import configure_api_defaults, stub_orchestrator_run_query


class DummyStorage:
    """In-memory stand-in for ``StorageManager`` used in CLI/API tests."""

    persisted: ClassVar[list[dict[str, object]]] = []

    @staticmethod
    def setup(db_path: str | None = None) -> None:
        DummyStorage.persist_claim(
            {
                "id": "dummy-claim-id",
                "type": "thesis",
                "content": "Dummy claim for testing",
            }
        )

    @staticmethod
    def persist_claim(claim: dict[str, object]) -> None:
        DummyStorage.persisted.append(dict(claim))


def _install_run_query_stub(monkeypatch: pytest.MonkeyPatch) -> None:
    def _runner(
        query: str,
        config: ConfigModel,
        callbacks: CallbackMap | None,
        extra: dict[str, Any],
    ) -> QueryResponse:
        from autoresearch.storage import set_delegate

        set_delegate(DummyStorage)
        DummyStorage.setup()
        if callbacks is not None and "on_cycle_end" in callbacks:
            state = QueryState(query=query)
            for index in range(config.loops):
                callbacks["on_cycle_end"](index, state)
        return QueryResponse(
            answer="# Answer\n\nDummy answer for testing",
            citations=[],
            reasoning=[],
            metrics={},
        )

    stub_orchestrator_run_query(monkeypatch, response=_runner)


def _common_patches(
    monkeypatch: pytest.MonkeyPatch, *, loops: int = 1
) -> ConfigModel:
    cfg = configure_api_defaults(monkeypatch, loops=loops)
    monkeypatch.setattr("autoresearch.llm.get_llm_adapter", lambda name: DummyAdapter())
    monkeypatch.setattr(
        "autoresearch.search.Search.external_lookup",
        lambda _query, max_results=5: [{"title": "t", "url": "u"}],
    )
    _install_run_query_stub(monkeypatch)
    monkeypatch.setattr(
        "autoresearch.storage.StorageManager.setup",
        staticmethod(lambda: None),
        raising=False,
    )
    return cfg


def _reset_storage() -> None:
    from autoresearch.storage import set_delegate

    set_delegate(None)
    DummyStorage.persisted = []


def test_cli_flow(monkeypatch: pytest.MonkeyPatch) -> None:
    """CLI search command renders responses using stubbed orchestrator."""

    _common_patches(monkeypatch)
    runner = CliRunner()
    monkeypatch.setattr("sys.stdout.isatty", lambda: True)

    DummyStorage.persist_claim(
        {"id": "dummy-claim-id", "type": "thesis", "content": "Dummy claim for testing"}
    )

    try:
        result = runner.invoke(cli_app, ["search", "test query", "--output", "markdown"])
        assert result.exit_code == 0
        assert "# Answer" in result.stdout
        assert DummyStorage.persisted
    finally:
        _reset_storage()


def test_http_flow(monkeypatch: pytest.MonkeyPatch) -> None:
    """HTTP query endpoint returns stubbed orchestrator responses."""

    _common_patches(monkeypatch)
    with TestClient(api_app) as client:
        DummyStorage.persist_claim(
            {"id": "dummy-claim-id", "type": "thesis", "content": "Dummy claim for testing"}
        )

        try:
            resp = client.post("/query", json={"query": "test query"})
            assert resp.status_code == 200
            data = resp.json()
            for key in ["answer", "citations", "reasoning", "metrics"]:
                assert key in data
            assert DummyStorage.persisted
        finally:
            _reset_storage()


def test_http_no_query_field(monkeypatch: pytest.MonkeyPatch) -> None:
    """Missing ``query`` field results in a validation error."""

    _common_patches(monkeypatch)
    with TestClient(api_app) as client:
        try:
            resp = client.post("/query", json={})
            assert resp.status_code == 422
            detail = resp.json()["detail"]
            assert detail[0]["msg"].startswith("Field required")
        finally:
            _reset_storage()


def test_cli_storage_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """CLI exits with code 1 when storage setup raises errors."""

    _common_patches(monkeypatch)
    runner = CliRunner()

    def fail_setup(*_args: object, **_kwargs: object) -> None:
        raise StorageError("boom")

    monkeypatch.setattr("autoresearch.storage.StorageManager.setup", fail_setup)

    result = runner.invoke(cli_app, ["search", "q"])

    assert result.exit_code == 1
    assert "Storage initialization failed" in result.stdout
    _reset_storage()


def test_http_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """API key and bearer token authentication succeed and fail appropriately."""

    cfg = _common_patches(monkeypatch)
    cfg.api.api_key = "secret"
    cfg.api.bearer_token = "token"
    with TestClient(api_app) as client:
        DummyStorage.persist_claim(
            {"id": "dummy-claim-id", "type": "thesis", "content": "Dummy claim for testing"}
        )

        try:
            resp = client.post(
                "/query",
                json={"query": "test query"},
                headers={"X-API-Key": "secret"},
            )
            assert resp.status_code == 200

            resp = client.post("/query", json={"query": "test query"})
            assert resp.status_code == 401
            assert resp.headers["WWW-Authenticate"] == "Bearer"

            resp = client.post(
                "/query",
                json={"query": "test query"},
                headers={"X-API-Key": "bad"},
            )
            assert resp.status_code == 401
            assert resp.headers["WWW-Authenticate"] == "API-Key"

            resp = client.post(
                "/query",
                json={"query": "test query"},
                headers={"Authorization": "Bearer token"},
            )
            assert resp.status_code == 200
        finally:
            _reset_storage()


def test_http_throttling(monkeypatch: pytest.MonkeyPatch) -> None:
    """Exceeding the configured rate limit returns HTTP 429."""

    cfg = _common_patches(monkeypatch)
    cfg.api.rate_limit = 1
    with TestClient(api_app) as client:
        DummyStorage.persist_claim(
            {"id": "dummy-claim-id", "type": "thesis", "content": "Dummy claim for testing"}
        )

        from autoresearch import api as api_mod

        try:
            resp1 = client.post("/query", json={"query": "test"})
            assert resp1.status_code == 200
            resp2 = client.post("/query", json={"query": "test"})
            assert resp2.status_code == 429
        finally:
            _reset_storage()
            api_mod.get_request_logger().reset()


def test_stream_endpoint(monkeypatch: pytest.MonkeyPatch) -> None:
    """Streaming endpoint yields cycle updates followed by final payload."""

    _common_patches(monkeypatch, loops=2)
    with TestClient(api_app) as client:
        with client.stream("POST", "/query/stream", json={"query": "q"}) as resp:
            assert resp.status_code == 200
            chunks = [line for line in resp.iter_lines()]

    assert len(chunks) == 3
    _reset_storage()


def test_webhook_notification(
    monkeypatch: pytest.MonkeyPatch, httpx_mock: Any
) -> None:
    """Final responses are POSTed to supplied webhook URLs."""

    _common_patches(monkeypatch)

    def _run_query(
        query: str,
        config: ConfigModel,
        callbacks: CallbackMap | None,
        extra: dict[str, Any],
    ) -> QueryResponse:
        return QueryResponse(answer="ok", citations=[], reasoning=[], metrics={})

    stub_orchestrator_run_query(monkeypatch, response=_run_query)
    with TestClient(api_app) as client:
        httpx_mock.add_response(method="POST", url="http://hook", status_code=200)
        resp = client.post("/query", json={"query": "hi", "webhook_url": "http://hook"})
        assert resp.status_code == 200
        assert len(httpx_mock.get_requests()) == 1
    _reset_storage()


def test_batch_query(monkeypatch: pytest.MonkeyPatch) -> None:
    """Batch query endpoint paginates results and returns per-query answers."""

    _common_patches(monkeypatch)

    def _echo_query(
        query: str,
        config: ConfigModel,
        callbacks: CallbackMap | None,
        extra: dict[str, Any],
    ) -> QueryResponse:
        return QueryResponse(answer=query, citations=[], reasoning=[], metrics={})

    stub_orchestrator_run_query(monkeypatch, response=_echo_query)
    with TestClient(api_app) as client:
        payload = {"queries": [{"query": "q1"}, {"query": "q2"}, {"query": "q3"}]}
        resp = client.post("/query/batch?page=1&page_size=2", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["page"] == 1
        assert len(data["results"]) == 2
        assert data["results"][0]["answer"] == "q1"
    _reset_storage()
