# mypy: ignore-errors
from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Iterator

from pytest import MonkeyPatch

from autoresearch.test_tools import A2ATestClient, MCPTestClient


@dataclass
class DummyResponse:
    """Simplified HTTP response used for testing the clients."""

    status_code: int = 200
    json_data: Any | Exception | None = None
    text: str = ""

    def json(self) -> Any:
        if isinstance(self.json_data, Exception):
            raise self.json_data
        return self.json_data


def test_mcp_test_connection(monkeypatch: MonkeyPatch) -> None:
    resp = DummyResponse(status_code=200, text="ok")

    def fake_get(*_: object, **__: object) -> DummyResponse:
        return resp

    monkeypatch.setattr("requests.get", fake_get)
    client = MCPTestClient()
    result = client.test_connection()
    assert result == {"status": "success", "status_code": 200, "content": "ok"}


def test_mcp_research_tool(monkeypatch: MonkeyPatch) -> None:
    resp = DummyResponse(status_code=200, json_data={"answer": "yes"})

    def fake_post(*_: object, **__: object) -> DummyResponse:
        return resp

    monkeypatch.setattr("requests.post", fake_post)
    times: Iterator[float] = iter([1.0, 2.0])

    def fake_time() -> float:
        return next(times)

    monkeypatch.setattr(time, "time", fake_time)
    client = MCPTestClient()
    result = client.test_research_tool("query")
    assert result["status"] == "success"
    assert result["status_code"] == 200
    assert result["response"] == {"answer": "yes"}
    assert result["time_taken"] == 1.0


def test_a2a_query(monkeypatch: MonkeyPatch) -> None:
    resp = DummyResponse(status_code=200, json_data={"reply": "ok"})

    def fake_post(*_: object, **__: object) -> DummyResponse:
        return resp

    monkeypatch.setattr("requests.post", fake_post)
    times: Iterator[float] = iter([1.0, 2.0])

    def fake_time() -> float:
        return next(times)

    monkeypatch.setattr(time, "time", fake_time)
    client = A2ATestClient()
    result = client.test_query("hi")
    assert result["status"] == "success"
    assert result["status_code"] == 200
    assert result["response"] == {"reply": "ok"}
    assert result["time_taken"] == 1.0


def test_a2a_capabilities(monkeypatch: MonkeyPatch) -> None:
    resp = DummyResponse(status_code=200, json_data={"capabilities": ["a"]})

    def fake_post(*_: object, **__: object) -> DummyResponse:
        return resp

    monkeypatch.setattr("requests.post", fake_post)
    times: Iterator[float] = iter([1.0, 2.0])

    def fake_time() -> float:
        return next(times)

    monkeypatch.setattr(time, "time", fake_time)
    client = A2ATestClient()
    result = client.test_capabilities()
    assert result["status"] == "success"
    assert result["status_code"] == 200
    assert result["response"] == {"capabilities": ["a"]}
    assert result["time_taken"] == 1.0


def test_run_test_suite(monkeypatch: MonkeyPatch) -> None:
    get_resp = DummyResponse(status_code=200, text="ok")
    post_resp = DummyResponse(status_code=200, json_data={"reply": "ok"})

    def fake_get(*_: object, **__: object) -> DummyResponse:
        return get_resp

    def fake_post(*_: object, **__: object) -> DummyResponse:
        return post_resp

    monkeypatch.setattr("requests.get", fake_get)
    monkeypatch.setattr("requests.post", fake_post)

    seq: Iterator[int] = iter(range(1, 10))

    def fake_time() -> float:
        return float(next(seq))

    monkeypatch.setattr(time, "time", fake_time)

    client = A2ATestClient()
    result = client.run_test_suite(["question"])
    assert result["connection_test"]["status"] == "success"
    assert result["capabilities_test"]["status"] == "success"
    assert result["query_tests"][0]["result"]["status"] == "success"
