import pytest

from autoresearch.monitor import metrics as monitor_metrics


@pytest.mark.asyncio
async def test_metrics_endpoint_decodes_prometheus_payload(monkeypatch):
    payload = b"sample_metric 1\n"

    monkeypatch.setattr(monitor_metrics, "generate_latest", lambda: payload)

    response = await monitor_metrics.metrics_endpoint()

    assert response.body == payload
    assert response.media_type == monitor_metrics.CONTENT_TYPE_LATEST
