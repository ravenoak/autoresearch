import pytest

from autoresearch.models import QueryResponse
from autoresearch.output_format import DepthPayload, build_depth_payload, OutputDepth
from autoresearch.ui.provenance import (
    audit_status_rollup,
    extract_graphrag_artifacts,
    generate_socratic_prompts,
    section_toggle_defaults,
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


def test_audit_status_rollup_orders_known_statuses(sample_payload) -> None:
    counts = audit_status_rollup(sample_payload.claim_audits)
    assert list(counts.keys())[0] == "supported"
    assert counts["supported"] == 1


def test_section_toggle_defaults_reflect_payload_sections(sample_payload) -> None:
    toggles = section_toggle_defaults(sample_payload)
    assert toggles["tldr"]["available"] is True
    assert toggles["key_findings"]["value"] is True
    assert toggles["claim_audits"]["available"] is True
    assert toggles["full_trace"]["available"] is True
