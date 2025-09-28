import json

import pytest

from autoresearch.cli_helpers import depth_help_text
from autoresearch.models import QueryResponse
from autoresearch.output_format import OutputDepth, OutputFormatter

pytestmark = pytest.mark.integration


@pytest.fixture
def response_payload() -> QueryResponse:
    return QueryResponse(
        query="depth test",
        answer="An extended answer about adaptive depth rendering.",
        citations=["Source A", "Source B"],
        reasoning=["Initial reasoning", "Follow-up check"],
        metrics={"tokens": 42, "latency_ms": 12},
        claim_audits=[
            {
                "claim_id": "1",
                "status": "supported",
                "entailment_score": 0.92,
                "sources": [{"title": "Whitepaper", "source_id": "src-1"}],
                "provenance": {
                    "retrieval": {"base_query": "depth test"},
                    "backoff": {"retry_count": 0},
                    "evidence": {"best_source_id": "src-1"},
                },
            }
        ],
    )


def test_cli_depth_tldr(response_payload: QueryResponse) -> None:
    output = OutputFormatter.render(response_payload, "markdown", OutputDepth.TLDR)
    assert "# TL;DR" in output
    assert "Key findings are hidden" in output


def test_cli_depth_trace_json(response_payload: QueryResponse) -> None:
    output = OutputFormatter.render(response_payload, "json", OutputDepth.TRACE)
    data = json.loads(output)
    assert data["sections"]["full_trace"] is True
    assert data["sections"]["claim_audits"] is True


def test_cli_preserves_claim_audits(response_payload: QueryResponse) -> None:
    output = OutputFormatter.render(response_payload, "json", OutputDepth.TRACE)
    payload = json.loads(output)
    assert payload["claim_audits"] == response_payload.claim_audits


def test_depth_help_text_includes_feature_matrix() -> None:
    text = depth_help_text()
    assert "includes TL;DR" in text
    assert "claim table" in text
    assert "full trace" in text
