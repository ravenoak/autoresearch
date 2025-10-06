# mypy: ignore-errors
import pytest
from autoresearch.orchestration.orchestrator import Orchestrator, ReasoningMode
from autoresearch.orchestration.orchestration_utils import OrchestrationUtils
from autoresearch.config.models import ConfigModel
from autoresearch.errors import NotFoundError


class DummyFactory:
    @staticmethod
    def get(name):
        raise RuntimeError("missing")


def test_get_agent_not_found():
    with pytest.raises(NotFoundError):
        OrchestrationUtils.get_agent("X", DummyFactory)


def test_parse_config_direct_mode():
    cfg = ConfigModel(reasoning_mode=ReasoningMode.DIRECT, loops=5)
    params = Orchestrator._parse_config(cfg)
    assert params["agents"] == ["Synthesizer"]
    assert params["loops"] == 1
    assert params["max_errors"] == 3


def test_parse_config_direct_mode_agent_groups():
    """Ensure direct mode uses only the Synthesizer group."""
    cfg = ConfigModel(reasoning_mode=ReasoningMode.DIRECT, loops=5)
    params = Orchestrator._parse_config(cfg)
    assert params["agent_groups"] == [["Synthesizer"]]
