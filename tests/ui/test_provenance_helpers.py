import pytest

from autoresearch.models import QueryResponse
from autoresearch.output_format import DepthPayload, build_depth_payload, OutputDepth
from autoresearch.ui.provenance import (
    extract_graphrag_artifacts,
    generate_socratic_prompts,
)

pytestmark = pytest.mark.requires_ui


@pytest.fixture
def sample_payload() -> DepthPayload:
    return build_depth_payload(
        QueryResponse(
            query="ui test",
            answer="Summary of the research findings.",
            citations=["Doc A"],
            reasoning=["Agent gathered documents", "Agents synthesised answer"],
            metrics={"tokens": 88, "graphrag_edges": [1, 2, 3]},
            claim_audits=[
                {
                    "claim_id": "alpha",
                    "status": "supported",
                    "entailment_score": 0.88,
                    "sources": [{"title": "Paper"}],
                }
            ],
        ),
        OutputDepth.STANDARD,
    )


def test_generate_socratic_prompts_highlight_claims(sample_payload) -> None:
    prompts = generate_socratic_prompts(sample_payload)
    assert prompts
    assert any("claim" in prompt.lower() for prompt in prompts)


def test_extract_graphrag_artifacts_filters_non_graph_metrics(sample_payload) -> None:
    artifacts = extract_graphrag_artifacts(sample_payload.metrics)
    assert "graphrag_edges" in artifacts
    assert "tokens" not in artifacts
