import asyncio
import socket
import sys
import time

import httpx
import pytest

# Ensure real a2a SDK is used instead of the test stub
try:  # pragma: no cover - best effort
    import pydantic.root_model as _rm  # noqa: E402
except Exception:  # pragma: no cover - fallback
    import types

    _rm = types.ModuleType("pydantic.root_model")
sys.modules.setdefault("pydantic.root_model", _rm)

for name in list(sys.modules):
    if name.startswith("a2a"):
        del sys.modules[name]

from a2a.types import Message  # noqa: E402
from a2a.utils.message import get_message_text, new_agent_text_message  # noqa: E402

from autoresearch.a2a_interface import A2A_AVAILABLE, A2AInterface  # noqa: E402
from autoresearch.config.loader import ConfigLoader  # noqa: E402
from autoresearch.config.models import ConfigModel  # noqa: E402

pytestmark = pytest.mark.skipif(not A2A_AVAILABLE, reason="A2A SDK not available")


@pytest.fixture
def running_server(monkeypatch):
    cfg = ConfigModel()
    monkeypatch.setattr(ConfigLoader, "load_config", lambda self: cfg)

    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    host, port = sock.getsockname()
    sock.close()

    interface = A2AInterface(host=host, port=port)

    start_times: list[float] = []

    def run_query(self, query, config, *_, **__):
        start_times.append(time.perf_counter())
        time.sleep(0.1)

        class Result:
            def __init__(self, answer: str) -> None:
                self.answer = answer

        return Result(f"answer for {query}")

    monkeypatch.setattr(
        "autoresearch.orchestration.orchestrator.Orchestrator.run_query",
        run_query,
    )

    interface.start()
    try:
        yield interface, start_times
    finally:
        interface.stop()


def _build_payload(text: str) -> dict:
    msg = new_agent_text_message(text)
    return {"type": "query", "message": msg.model_dump(mode="json")}


@pytest.mark.slow
def test_concurrent_queries(running_server):
    interface, start_times = running_server
    url = f"http://{interface.host}:{interface.port}/"

    async def send_all() -> list[dict]:
        async with httpx.AsyncClient() as client:
            tasks = [client.post(url, json=_build_payload(f"q{i}")) for i in range(3)]
            responses = await asyncio.gather(*tasks)
            for resp in responses:
                resp.raise_for_status()
        return [resp.json() for resp in responses]

    results = asyncio.run(send_all())
    assert len(results) == 3
    assert len(start_times) == 3
    for i, data in enumerate(results):
        assert data["status"] == "success"
        msg = Message.model_validate(data["message"])
        assert get_message_text(msg) == f"answer for q{i}"

    assert max(start_times) - min(start_times) < 0.05
