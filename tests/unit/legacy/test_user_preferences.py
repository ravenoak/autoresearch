import tomli_w
import pytest
from unittest.mock import patch, MagicMock

from autoresearch.agents.specialized.user_agent import UserAgent
from autoresearch.config.models import ConfigModel
from autoresearch.config.loader import ConfigLoader
from autoresearch.orchestration.state import QueryState


@pytest.fixture
def simple_state():
    # Reset preferences between tests
    UserAgent.preferences = {
        "detail_level": "balanced",
        "perspective": "neutral",
        "format_preference": "structured",
        "expertise_level": "intermediate",
        "focus_areas": [],
        "excluded_areas": [],
    }
    state = QueryState(query="example")
    state.claims = [{"id": "1", "type": "thesis", "content": "c"}]
    state.cycle = 1
    return state


def test_user_agent_loads_preferences(monkeypatch, simple_state):
    mock_adapter = MagicMock()
    mock_adapter.generate.return_value = "resp"
    with patch("autoresearch.llm.get_pooled_adapter", return_value=mock_adapter):
        cfg = ConfigModel(user_preferences={"detail_level": "detailed", "focus_areas": ["ai"]})
        agent = UserAgent(name="User")
        result = agent.execute(simple_state, cfg)

    assert result["metadata"]["user_preferences"]["detail_level"] == "detailed"
    assert result["metadata"]["user_preferences"]["focus_areas"] == ["ai"]


def test_user_preferences_hot_reload(example_autoresearch_toml, monkeypatch, simple_state):
    ConfigLoader.reset_instance()
    cfg_path = example_autoresearch_toml
    cfg_path.write_text(
        tomli_w.dumps(
            {"core": {"loops": 1}, "user_preferences": {"detail_level": "concise"}}
        )
    )

    loader = ConfigLoader()
    loader._config = loader.load_config()
    loader._update_watch_paths()
    loader.watch_changes()

    mock_adapter = MagicMock()
    mock_adapter.generate.return_value = "resp"
    with patch("autoresearch.llm.get_pooled_adapter", return_value=mock_adapter):
        agent = UserAgent(name="User")
        first = agent.execute(simple_state, loader.config)
        first_prefs = first["metadata"]["user_preferences"].copy()

        cfg_path.write_text(tomli_w.dumps({"core": {"loops": 1}, "user_preferences": {"detail_level": "detailed"}}))
        loader._config = loader.load_config()
        second = agent.execute(simple_state, loader.config)

    assert first_prefs["detail_level"] == "concise"
    assert second["metadata"]["user_preferences"]["detail_level"] == "detailed"
