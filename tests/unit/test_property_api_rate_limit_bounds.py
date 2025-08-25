from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient
from hypothesis import given
from hypothesis import strategies as st

from autoresearch.api.middleware import FallbackRateLimitMiddleware, Limiter
from autoresearch.api.utils import RequestLogger
from autoresearch.config.loader import ConfigLoader
from autoresearch.config.models import APIConfig, ConfigModel


@given(limit=st.integers(min_value=1, max_value=5), requests=st.integers(min_value=0, max_value=10))
def test_rate_limit_bounds(limit: int, requests: int) -> None:
    with ConfigLoader.temporary_instance() as loader:
        loader._config = ConfigModel(api=APIConfig(rate_limit=limit))
        app = FastAPI()
        app.state.config_loader = loader
        logger = RequestLogger()
        limiter = Limiter(key_func=lambda _r: "test")
        app.add_middleware(FallbackRateLimitMiddleware, request_logger=logger, limiter=limiter)

        @app.get("/health")
        def _health() -> dict[str, str]:
            return {"status": "ok"}

        client = TestClient(app)
        responses = [client.get("/health") for _ in range(requests)]
        allowed = sum(r.status_code == 200 for r in responses)
        assert allowed <= limit
        if requests > limit:
            assert responses[-1].status_code == 429
