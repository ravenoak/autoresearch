from __future__ import annotations

import pytest

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


def test_query_state_update_validates_payload_shapes() -> None:
    """Ensure ``QueryState.update`` enforces mapping and sequence contracts."""

    state = QueryState(query="validate")

    with pytest.raises(TypeError):
        state.update({"claims": {"id": "c1"}})

    with pytest.raises(TypeError):
        state.update({"sources": ["not-a-mapping"]})

    with pytest.raises(TypeError):
        state.update({"metadata": [("key", "value")]})

    with pytest.raises(TypeError):
        state.update({"results": ["oops"]})


def test_task_graph_normalization_logs_react_entries() -> None:
    """``set_task_graph`` records normalization warnings in the react log."""

    state = QueryState(query="react-log")
    warnings = state.set_task_graph(
        {
            "tasks": [
                {
                    "question": "Investigate topic",
                    "tools": {"primary": "search"},
                    "depends_on": ["ghost"],
                    "affinity": "search:high",
                }
            ],
            "edges": [
                {
                    "source": "ghost",
                    "target": "task-1",
                }
            ],
        }
    )
    assert warnings
    assert any(entry["event"] == "planner.normalization" for entry in state.react_log)

    state.record_planner_trace(
        prompt="Plan?",
        raw_response="{}",
        normalized=state.task_graph,
        warnings=warnings,
    )
    assert state.react_log[-1]["event"] == "planner.trace"
    assert state.react_log[-1]["metadata"]["warnings"]

    state.set_task_graph({"tasks": [{"id": "clean", "question": "Done"}]})
    assert len(state.react_log) >= 2


def test_task_graph_telemetry_persists() -> None:
    """Planner telemetry is captured and survives serialization."""

    state = QueryState(query="telemetry")
    payload = {
        "objectives": ["Understand the research landscape"],
        "exit_criteria": ["All findings validated"],
        "tasks": [
            {
                "id": "scope",
                "question": "Define project scope",
                "objectives": ["List constraints"],
                "tools": ["planning"],
                "tool_affinity": {"planning": 0.8},
                "exit_criteria": ["Stakeholders aligned"],
                "explanation": "Clarifies success metrics",
            }
        ],
    }
    state.set_task_graph(payload)
    telemetry = state.metadata["planner"]["telemetry"]
    assert telemetry["objectives"] == ["Understand the research landscape"]
    assert telemetry["exit_criteria"] == ["All findings validated"]
    assert telemetry["tasks"][0]["objectives"] == ["List constraints"]
    assert telemetry["tasks"][0]["tool_affinity"]["planning"] == 0.8
    assert telemetry["tasks"][0]["exit_criteria"] == ["Stakeholders aligned"]
    assert telemetry["tasks"][0]["explanation"] == "Clarifies success metrics"

    telemetry_events = [
        entry for entry in state.react_log if entry["event"] == "planner.telemetry"
    ]
    assert telemetry_events, "planner telemetry should be logged to the react log"
    latest = telemetry_events[-1]["payload"]
    assert latest["telemetry"]["tasks"][0]["exit_criteria"] == [
        "Stakeholders aligned"
    ]
    assert latest["task_graph_stats"]["task_count"] == 1

    cloudpickle = pytest.importorskip("cloudpickle")
    restored = cloudpickle.loads(cloudpickle.dumps(state))
    assert restored.metadata["planner"]["telemetry"] == telemetry
