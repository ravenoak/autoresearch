import threading

from fastapi.testclient import TestClient

from autoresearch.api import app, dynamic_limit
from autoresearch.config.loader import ConfigLoader
from autoresearch.config.models import APIConfig, ConfigModel
from autoresearch.models import QueryResponse
from autoresearch.orchestration.orchestrator import Orchestrator


def _setup(monkeypatch):
    cfg = ConfigModel.model_construct(api=APIConfig())
    cfg.api.role_permissions["anonymous"] = ["query"]
    monkeypatch.setattr(ConfigLoader, "load_config", lambda self: cfg)
    monkeypatch.setattr(
        Orchestrator,
        "run_query",
        lambda q, c, callbacks=None, **k: QueryResponse(
            answer="ok", citations=[], reasoning=[], metrics={}
        ),
    )
    # Ensure the request log starts from a clean state. Import lazily so tests
    # can control how the API module is initialised.
    from autoresearch.api import reset_request_log

    reset_request_log()
    return cfg


def test_dynamic_limit(monkeypatch):
    cfg = _setup(monkeypatch)
    cfg.api.rate_limit = 5
    assert dynamic_limit() == "5/minute"
    cfg.api.rate_limit = 0
    assert dynamic_limit() == "1000000/minute"


def test_api_key_roles(monkeypatch):
    cfg = _setup(monkeypatch)
    cfg.api.api_keys = {"secret": "user"}
    client = TestClient(app)

    resp = client.post("/query", json={"query": "q"}, headers={"X-API-Key": "secret"})
    assert resp.status_code == 200

    resp = client.post("/query", json={"query": "q"}, headers={"X-API-Key": "bad"})
    assert resp.status_code == 401


def test_batch_query_invalid_page(monkeypatch):
    _setup(monkeypatch)
    client = TestClient(app)
    payload = {"queries": [{"query": "q1"}]}
    resp = client.post("/query/batch?page=0&page_size=1", json=payload)
    assert resp.status_code == 400


def test_fallback_no_limit(monkeypatch):
    cfg = _setup(monkeypatch)
    cfg.api.rate_limit = 0

    from autoresearch import api as api_mod

    api_mod.reset_request_log()
    monkeypatch.setattr(
        "autoresearch.api.routing.get_remote_address",
        lambda req: req.headers.get("x-ip", "1"),
    )
    client = TestClient(app)

    assert client.post("/query", json={"query": "q"}).status_code == 200
    assert client.post("/query", json={"query": "q"}).status_code == 200
    assert api_mod.get_request_logger().snapshot() == {}


def test_fallback_multiple_ips(monkeypatch):
    cfg = _setup(monkeypatch)
    cfg.api.rate_limit = 1

    from autoresearch import api as api_mod

    api_mod.reset_request_log()

    def addr(req):
        return req.headers.get("x-ip", "1")

    monkeypatch.setattr("autoresearch.api.routing.get_remote_address", addr)
    client = TestClient(app)
    limit_obj = api_mod.parse(api_mod.dynamic_limit())

    assert (
        client.post("/query", json={"query": "q"}, headers={"x-ip": "1"}).status_code
        == 200
    )
    if api_mod.SLOWAPI_STUB:
        assert api_mod.get_request_logger().get("1") == 1
    else:
        assert api_mod.limiter.limiter.get_window_stats(limit_obj, "1")[1] == 0

    assert (
        client.post("/query", json={"query": "q"}, headers={"x-ip": "2"}).status_code
        == 200
    )
    if api_mod.SLOWAPI_STUB:
        assert api_mod.get_request_logger().get("2") == 1
    else:
        assert api_mod.limiter.limiter.get_window_stats(limit_obj, "2")[1] == 0

    assert (
        client.post("/query", json={"query": "q"}, headers={"x-ip": "1"}).status_code
        == 429
    )
    if api_mod.SLOWAPI_STUB:
        assert api_mod.get_request_logger().get("1") == 2
    else:
        assert api_mod.limiter.limiter.get_window_stats(limit_obj, "1")[1] == 0


def test_request_log_thread_safety(monkeypatch):
    cfg = _setup(monkeypatch)
    cfg.api.rate_limit = 0

    from autoresearch import api as api_mod

    api_mod.reset_request_log()

    results: list[int] = []

    def make_request() -> None:
        results.append(api_mod.get_request_logger().log("1"))

    threads = [threading.Thread(target=make_request) for _ in range(20)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert all(isinstance(r, int) for r in results)

    count = api_mod.get_request_logger().get("1")
    assert isinstance(count, int)
    assert count == 20

    missing = api_mod.get_request_logger().get("2")
    assert isinstance(missing, int)
    assert missing == 0
