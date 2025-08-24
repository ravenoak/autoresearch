from autoresearch.agents.specialized.critic import CriticAgent
from autoresearch.config.models import ConfigModel
from autoresearch.orchestration.state import QueryState


def test_can_execute_requires_claims():
    agent = CriticAgent()
    config = ConfigModel()
    assert not agent.can_execute(QueryState(query=""), config)
    state = QueryState(query="q", claims=[{"content": "data"}])
    assert agent.can_execute(state, config)


def test_execute_generates_critique(monkeypatch):
    state = QueryState(
        query="q",
        claims=[{"id": "1", "type": "research_findings", "content": "data"}],
    )
    config = ConfigModel()
    agent = CriticAgent()

    class DummyAdapter:
        def generate(self, prompt, model=None):
            assert prompt == "prompt"
            return "critique text"

    monkeypatch.setattr(
        CriticAgent, "get_adapter", lambda self, cfg: DummyAdapter()
    )
    monkeypatch.setattr(
        CriticAgent, "generate_prompt", lambda self, name, **kw: "prompt"
    )

    result = agent.execute(state, config)

    assert result["results"]["critique"] == "critique text"
    assert result["claims"][0]["type"] == "critique"
