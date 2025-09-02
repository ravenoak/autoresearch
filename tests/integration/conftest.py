import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from autoresearch.api import app as api_app

BASELINE_FILE = Path(__file__).resolve().parents[1] / "data" / "token_baselines.json"
METRIC_BASELINE_FILE = Path(__file__).resolve().parents[1] / "data" / "backend_metrics.json"
SEARCH_BASELINE_FILE = Path(__file__).resolve().parents[1] / "data" / "search_baselines.json"


@pytest.fixture
def api_client():
    """Provide a FastAPI TestClient that closes after use."""
    with TestClient(api_app) as client:
        yield client


@pytest.fixture
def token_baseline(request):
    """Record and compare token usage across test runs."""

    def _check(tokens, tolerance: int = 0) -> None:
        data = json.loads(BASELINE_FILE.read_text()) if BASELINE_FILE.exists() else {}
        test_id = request.node.nodeid
        baseline = data.get(test_id)
        if baseline is not None:
            for agent, counts in tokens.items():
                base_counts = baseline.get(agent, {})
                for direction in ("in", "out"):
                    measured = counts.get(direction, 0)
                    expected = base_counts.get(direction, 0)
                    delta = abs(measured - expected)
                    assert (
                        delta <= tolerance
                    ), f"{test_id} {agent} {direction} delta {delta} exceeds tolerance {tolerance}"
        data[test_id] = tokens
        BASELINE_FILE.write_text(json.dumps(data, indent=2, sort_keys=True))

    return _check


@pytest.fixture
def metrics_baseline(request):
    """Record and compare backend metrics across test runs."""

    def _check(
        backend: str,
        precision: float,
        recall: float,
        latency: float,
        tolerance: float = 0.05,
    ) -> None:
        data = json.loads(METRIC_BASELINE_FILE.read_text()) if METRIC_BASELINE_FILE.exists() else {}
        key = f"{request.node.nodeid}::{backend}"
        baseline = data.get(key)
        if baseline is not None:
            assert precision >= baseline["precision"] - tolerance
            assert recall >= baseline["recall"] - tolerance
            assert latency <= baseline["latency"] * (1 + tolerance)
        data[key] = {
            "precision": precision,
            "recall": recall,
            "latency": latency,
        }
        METRIC_BASELINE_FILE.write_text(json.dumps(data, indent=2, sort_keys=True))

    return _check


@pytest.fixture
def search_baseline(request):
    """Record and compare search results across test runs."""

    def _check(results):
        data = json.loads(SEARCH_BASELINE_FILE.read_text()) if SEARCH_BASELINE_FILE.exists() else {}
        key = request.node.nodeid
        current = [{"title": r["title"], "url": r["url"]} for r in results]
        baseline = data.get(key)
        if baseline is not None:
            assert current == baseline
        data[key] = current
        SEARCH_BASELINE_FILE.write_text(json.dumps(data, indent=2, sort_keys=True))

    return _check
