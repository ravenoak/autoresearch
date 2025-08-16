import pytest
from types import SimpleNamespace

from autoresearch.orchestration.orchestrator import Orchestrator
from autoresearch.orchestration import metrics


@pytest.fixture
def orchestrator_runner():
    """Return a factory for creating fresh ``Orchestrator`` instances."""

    def _factory() -> Orchestrator:
        return Orchestrator()

    return _factory


@pytest.fixture(autouse=True)
def reset_orchestration_metrics():
    """Reset global metrics counters before and after each test."""

    class DummyCounter:
        def __init__(self) -> None:
            self._value = SimpleNamespace(
                value=0, get=lambda: self._value.value, set=self._set
            )

        def _set(self, v: int) -> None:
            self._value.value = v

        def inc(self, n: int = 1) -> None:
            self._value.value += n

    names = [
        "QUERY_COUNTER",
        "ERROR_COUNTER",
        "TOKENS_IN_COUNTER",
        "TOKENS_OUT_COUNTER",
    ]
    for name in names:
        counter = getattr(metrics, name, None)
        if not hasattr(counter, "_value") or not hasattr(counter, "inc"):
            counter = DummyCounter()
            setattr(metrics, name, counter)
        counter._value.set(0)
    yield
    for name in names:
        counter = getattr(metrics, name)
        counter._value.set(0)
