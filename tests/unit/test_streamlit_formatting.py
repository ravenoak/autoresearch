import json
from hypothesis import given, strategies as st
from autoresearch.streamlit_app import (
    create_interaction_trace,
    create_progress_graph,
    format_result_as_markdown,
    format_result_as_json,
)
from autoresearch.models import QueryResponse
from typing import Any


@given(st.lists(st.text(min_size=1, max_size=20), max_size=5))
def test_create_interaction_trace_contains_steps(steps: Any) -> None:
    graph = create_interaction_trace(steps)
    assert graph.startswith("digraph Trace")
    for idx, step in enumerate(steps, start=1):
        label = step.replace("\n", "").replace('"', "")[:20]
        assert label in graph
        assert f"step{idx}" in graph


@given(st.dictionaries(st.text(min_size=1, max_size=5), st.integers(min_value=0, max_value=5), min_size=1, max_size=4))
def test_create_progress_graph(agent_execs: Any) -> None:
    perf = {k: {"executions": v} for k, v in agent_execs.items()}
    graph = create_progress_graph(perf)
    assert graph.startswith("digraph Progress")
    for name in perf:
        assert name in graph
    agents = list(perf.keys())
    if len(agents) > 1:
        assert f'"{agents[0]}" -> "{agents[1]}"' in graph


@given(
    answer=st.text(min_size=1, max_size=30),
    citations=st.lists(st.text(min_size=1, max_size=15), max_size=3),
    reasoning=st.lists(st.text(min_size=1, max_size=15), max_size=3),
)
def test_format_result_markdown_json(answer: Any, citations: Any, reasoning: Any) -> None:
    resp = QueryResponse(answer=answer, citations=citations, reasoning=reasoning, metrics={})
    md = format_result_as_markdown(resp)
    assert answer in md
    for c in citations:
        assert c in md
    js = format_result_as_json(resp)
    parsed = json.loads(js)
    assert parsed["answer"] == answer
    assert parsed["citations"] == citations
    assert parsed["reasoning"] == reasoning
