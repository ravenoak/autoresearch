from __future__ import annotations

from autoresearch.agents.feedback import FeedbackEvent
from autoresearch.agents.messages import MessageProtocol
from autoresearch.orchestration.state import QueryState


def test_query_state_update_and_retrieval() -> None:
    """Ensure QueryState updates and retrieves information correctly."""
    state = QueryState(query="What is AI?")

    result = {
        "claims": [{"content": "A claim", "type": "thesis"}],
        "sources": [{"url": "http://example.com"}],
        "metadata": {"score": 1},
        "results": {"final_answer": "Answer"},
    }
    state.update(result)

    state.add_error({"detail": "oops"})
    state.add_message(
        {
            "from": "agent",
            "to": "recipient",
            "protocol": MessageProtocol.DIRECT.value,
            "content": "hi",
        }
    )
    event = FeedbackEvent(source="a", target="b", content="c", cycle=0)
    state.add_feedback_event(event)
    state.add_coalition("team", ["agent"])

    assert state.claims and state.sources and state.metadata["score"] == 1
    assert state.results["final_answer"] == "Answer"
    assert state.error_count == 1
    assert state.get_feedback_events(recipient="b") == [event]
    assert state.get_coalition_members("team") == ["agent"]
    msgs = state.get_messages(recipient="recipient")
    assert msgs and msgs[0]["content"] == "hi"

    synth = state.synthesize()
    assert synth.answer == "Answer"
    structure = state.get_dialectical_structure()
    assert structure["thesis"]["content"] == "A claim"

    state.prune_context(max_claims=0, max_sources=0, max_messages=0, max_feedback=0)
    assert state.metadata["pruned"][0] == {
        "claims": 1,
        "sources": 1,
        "messages": 1,
        "feedback": 1,
    }
