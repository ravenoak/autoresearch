from autoresearch.agents.specialized.planner import PlannerPromptBuilder


def test_planner_prompt_builder_injects_graph_context() -> None:
    """Graph context is summarised in the planner prompt when provided."""

    graph_context = {
        "contradictions": {
            "weighted_score": 0.28,
            "raw_score": 0.8,
            "items": [
                {
                    "subject": "Policy A",
                    "predicate": "conflicts_with",
                    "objects": ["Policy B"],
                }
            ],
        },
        "similarity": {"weighted_score": 0.1, "raw_score": 0.2},
        "neighbors": {
            "Policy A": [
                {
                    "predicate": "relates_to",
                    "target": "Policy C",
                    "direction": "out",
                }
            ]
        },
        "paths": [["Policy A", "Policy B", "Policy C"]],
        "sources": ["https://example.com/policy-a"],
        "provenance": [{"source": "https://example.com/policy-a"}],
    }

    prompt = PlannerPromptBuilder(
        base_prompt="Planner base",
        query="Policy impact",
        graph_context=graph_context,
    ).build()

    assert "Knowledge graph signals:" in prompt
    assert "Graph similarity support: 0.10 (raw 0.20)" in prompt
    assert "Contradiction score: 0.28 (raw 0.80)" in prompt
    assert "Policy A --conflicts_with--> Policy B" in prompt
    assert "Representative neighbours" in prompt
    assert "Policy A → (relates_to) Policy C" in prompt
    assert "Multi-hop paths" in prompt
    assert "Policy A → Policy B → Policy C" in prompt
    assert "Provenance sources: https://example.com/policy-a" in prompt


def test_planner_prompt_builder_without_graph_context() -> None:
    """No graph summary is included when graph context is absent."""

    prompt = PlannerPromptBuilder(
        base_prompt="Planner base",
        query="Policy impact",
    ).build()

    assert "Knowledge graph signals:" not in prompt
