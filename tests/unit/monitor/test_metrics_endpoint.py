import asyncio
import pytest

from autoresearch.monitor import metrics as monitor_metrics


def test_metrics_endpoint_decodes_prometheus_payload(monkeypatch):
    payload = b"sample_metric 1\n"

    monkeypatch.setattr(monitor_metrics, "generate_latest", lambda: payload)

    response = asyncio.run(monitor_metrics.metrics_endpoint())

    assert response.status_code == 200
    assert response.body.decode() == "sample_metric 1\n"
    assert response.media_type == monitor_metrics.CONTENT_TYPE_LATEST


def test_metrics_endpoint_coerces_bytearray(monkeypatch):
    payload = bytearray(b"another_metric 2\n")

    monkeypatch.setattr(monitor_metrics, "generate_latest", lambda: payload)

    response = asyncio.run(monitor_metrics.metrics_endpoint())

    assert response.status_code == 200
    assert response.body.decode() == "another_metric 2\n"


def test_metrics_endpoint_handles_failure(monkeypatch):
    def _boom() -> bytes:
        raise RuntimeError("nope")

    monkeypatch.setattr(monitor_metrics, "generate_latest", _boom)

    response = asyncio.run(monitor_metrics.metrics_endpoint())

    assert response.status_code == 503
    assert "metrics_unavailable" in response.body.decode()
