import time
from autoresearch.test_tools import MCPTestClient, A2ATestClient


class DummyResponse:
    def __init__(self, status_code=200, json_data=None, text=""):
        self.status_code = status_code
        self._json = json_data
        self.text = text

    def json(self):
        if isinstance(self._json, Exception):
            raise self._json
        return self._json


def test_mcp_test_connection(monkeypatch):
    resp = DummyResponse(status_code=200, text="ok")
    monkeypatch.setattr("requests.get", lambda *_a, **_k: resp)
    client = MCPTestClient()
    result = client.test_connection()
    assert result == {"status": "success", "status_code": 200, "content": "ok"}


def test_mcp_research_tool(monkeypatch):
    resp = DummyResponse(status_code=200, json_data={"answer": "yes"})
    monkeypatch.setattr("requests.post", lambda *_a, **_k: resp)
    times = iter([1.0, 2.0])
    monkeypatch.setattr(time, "time", lambda: next(times))
    client = MCPTestClient()
    result = client.test_research_tool("query")
    assert result["status"] == "success"
    assert result["status_code"] == 200
    assert result["response"] == {"answer": "yes"}
    assert result["time_taken"] == 1.0


def test_a2a_query(monkeypatch):
    resp = DummyResponse(status_code=200, json_data={"reply": "ok"})
    monkeypatch.setattr("requests.post", lambda *_a, **_k: resp)
    times = iter([1.0, 2.0])
    monkeypatch.setattr(time, "time", lambda: next(times))
    client = A2ATestClient()
    result = client.test_query("hi")
    assert result["status"] == "success"
    assert result["status_code"] == 200
    assert result["response"] == {"reply": "ok"}
    assert result["time_taken"] == 1.0


def test_a2a_capabilities(monkeypatch):
    resp = DummyResponse(status_code=200, json_data={"capabilities": ["a"]})
    monkeypatch.setattr("requests.post", lambda *_a, **_k: resp)
    times = iter([1.0, 2.0])
    monkeypatch.setattr(time, "time", lambda: next(times))
    client = A2ATestClient()
    result = client.test_capabilities()
    assert result["status"] == "success"
    assert result["status_code"] == 200
    assert result["response"] == {"capabilities": ["a"]}
    assert result["time_taken"] == 1.0


def test_run_test_suite(monkeypatch):
    get_resp = DummyResponse(status_code=200, text="ok")
    post_resp = DummyResponse(status_code=200, json_data={"reply": "ok"})

    monkeypatch.setattr("requests.get", lambda *_a, **_k: get_resp)
    monkeypatch.setattr("requests.post", lambda *_a, **_k: post_resp)

    seq = iter(range(1, 10))
    monkeypatch.setattr(time, "time", lambda: next(seq))

    client = A2ATestClient()
    result = client.run_test_suite(["question"])
    assert result["connection_test"]["status"] == "success"
    assert result["capabilities_test"]["status"] == "success"
    assert result["query_tests"][0]["result"]["status"] == "success"
