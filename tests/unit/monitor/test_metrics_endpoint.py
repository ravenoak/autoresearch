import asyncio
from autoresearch.monitor import metrics as monitor_metrics
import pytest


def test_metrics_endpoint_decodes_prometheus_payload(monkeypatch: pytest.MonkeyPatch) -> None:
    payload = b"sample_metric 1\n"

    monkeypatch.setattr(monitor_metrics, "generate_latest", lambda: payload)

    response = asyncio.run(monitor_metrics.metrics_endpoint())

    assert response.status_code == 200
    assert response.body.decode() == "sample_metric 1\n"
    assert response.media_type == monitor_metrics.CONTENT_TYPE_LATEST


def test_metrics_endpoint_coerces_bytearray(monkeypatch: pytest.MonkeyPatch) -> None:
    payload = bytearray(b"another_metric 2\n")

    monkeypatch.setattr(monitor_metrics, "generate_latest", lambda: payload)

    response = asyncio.run(monitor_metrics.metrics_endpoint())

    assert response.status_code == 200
    assert response.body.decode() == "another_metric 2\n"


def test_metrics_endpoint_handles_memoryview(monkeypatch: pytest.MonkeyPatch) -> None:
    payload = memoryview(b"view_metric 3\n")

    monkeypatch.setattr(monitor_metrics, "generate_latest", lambda: payload)

    response = asyncio.run(monitor_metrics.metrics_endpoint())

    assert response.status_code == 200
    assert response.body.decode() == "view_metric 3\n"


def test_metrics_endpoint_replaces_invalid_bytes(monkeypatch: pytest.MonkeyPatch) -> None:
    payload = b"bad_metric \xff\n"

    monkeypatch.setattr(monitor_metrics, "generate_latest", lambda: payload)

    response = asyncio.run(monitor_metrics.metrics_endpoint())

    assert response.status_code == 200
    assert response.body.decode() == "bad_metric \ufffd\n"


def test_metrics_endpoint_handles_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    def _boom() -> bytes:
        raise RuntimeError("nope")

    monkeypatch.setattr(monitor_metrics, "generate_latest", _boom)

    response = asyncio.run(monitor_metrics.metrics_endpoint())

    assert response.status_code == 503
    assert "metrics_unavailable" in response.body.decode()
