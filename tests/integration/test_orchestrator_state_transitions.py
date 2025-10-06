# mypy: ignore-errors
from autoresearch.models import QueryResponse
from autoresearch.orchestration.state import QueryState


def test_state_update_transition() -> None:
    state = QueryState(query="q")
    before = state.last_updated
    state.update(
        {
            "claims": [{"id": "c1", "type": "fact", "content": "ok"}],
            "results": {"Synthesizer": "ok"},
        }
    )
    assert state.claims and state.results["Synthesizer"] == "ok"
    assert state.last_updated >= before


def test_state_error_transition() -> None:
    state = QueryState(query="q")
    state.add_error({"msg": "fail"})
    assert state.error_count == 1
    assert state.metadata["errors"][0]["msg"] == "fail"


def test_state_error_recovery_transition() -> None:
    state = QueryState(query="q")
    state.add_error({"msg": "fail"})
    state.update({"results": {"Synthesizer": "ok"}})
    assert state.error_count == 1
    assert state.results["Synthesizer"] == "ok"


def test_state_synthesis_transition() -> None:
    state = QueryState(query="q")
    state.update(
        {
            "results": {"final_answer": "ans"},
            "sources": [{"id": 1}],
            "claims": [{"type": "synthesis", "content": "done"}],
        }
    )
    response = state.synthesize()
    assert isinstance(response, QueryResponse)
    assert response.answer == "ans"
    assert response.citations and response.reasoning
