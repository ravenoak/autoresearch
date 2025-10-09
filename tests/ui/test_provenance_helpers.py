from __future__ import annotations

from typing import Mapping, cast

import pytest

from autoresearch.models import QueryResponse
from autoresearch.output_format import DepthPayload, build_depth_payload, OutputDepth
from autoresearch.ui.provenance import (
    audit_status_rollup,
    depth_sequence,
    extract_graphrag_artifacts,
    format_gate_rationales,
    generate_socratic_prompts,
    section_toggle_defaults,
    triggered_gate_signals,
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


def test_generate_socratic_prompts_highlight_claims(sample_payload: DepthPayload) -> None:
    prompts = generate_socratic_prompts(sample_payload)
    assert prompts
    assert any("claim" in prompt.lower() for prompt in prompts)


def test_extract_graphrag_artifacts_filters_non_graph_metrics(
    sample_payload: DepthPayload,
) -> None:
    artifacts = extract_graphrag_artifacts(sample_payload.metrics)
    assert "graphrag_edges" in artifacts
    assert "tokens" not in artifacts


def test_audit_status_rollup_orders_known_statuses(sample_payload: DepthPayload) -> None:
    claim_audits = cast(list[Mapping[str, object]], list(sample_payload.claim_audits))
    counts = audit_status_rollup(claim_audits)
    assert list(counts.keys())[0] == "supported"
    assert counts["supported"] == 1


def test_section_toggle_defaults_reflect_payload_sections(
    sample_payload: DepthPayload,
) -> None:
    toggles = section_toggle_defaults(sample_payload)
    assert toggles["tldr"]["available"] is True
    assert toggles["key_findings"]["value"] is True
    assert toggles["claim_audits"]["available"] is True
    assert toggles["full_trace"]["available"] is True
    assert toggles["knowledge_graph"]["available"] is False
    assert toggles["graph_exports"]["available"] is False


def test_depth_sequence_returns_ordered_depths() -> None:
    """Test that depth_sequence returns depths in UI order."""
    depths = depth_sequence()
    assert depths == [
        OutputDepth.TLDR,
        OutputDepth.CONCISE,
        OutputDepth.STANDARD,
        OutputDepth.TRACE,
    ]


def test_triggered_gate_signals_extracts_triggered_signals() -> None:
    """Test extraction of triggered gate signals."""
    snapshot = {
        "rationales": {
            "low_confidence": {"triggered": True, "reason": "Low confidence"},
            "high_uncertainty": {"triggered": False, "reason": "High uncertainty"},
            "missing_evidence": {"triggered": True, "reason": "Missing evidence"},
        }
    }
    signals = triggered_gate_signals(snapshot)
    assert "low confidence" in signals
    assert "missing evidence" in signals
    assert "high uncertainty" not in signals


def test_triggered_gate_signals_handles_empty_snapshot() -> None:
    """Test triggered_gate_signals with empty or invalid snapshots."""
    assert triggered_gate_signals({}) == []
    assert triggered_gate_signals({"rationales": "not_a_dict"}) == []
    assert triggered_gate_signals({"rationales": {}}) == []


def test_format_gate_rationales_builds_readable_rationales() -> None:
    """Test formatting of gate rationales into human-readable form."""
    snapshot = {
        "rationales": {
            "low_confidence": {
                "triggered": True,
                "value": 0.5,
                "threshold": 0.7,
                "description": "Answer confidence below threshold",
            },
            "high_uncertainty": {
                "triggered": False,
                "value": 0.8,
                "threshold": 0.9,
                "description": "High uncertainty detected",
            },
        }
    }
    rationales = format_gate_rationales(snapshot)
    assert len(rationales) == 2  # All rationales, triggered and not
    # Check triggered rationale
    triggered = [r for r in rationales if "triggered" in r.lower()]
    assert len(triggered) == 1
    assert "low confidence" in triggered[0].lower()
    assert "0.50" in triggered[0]  # formatted value
    assert "0.70" in triggered[0]  # formatted threshold
    # Check within threshold rationale
    within = [r for r in rationales if "within threshold" in r.lower()]
    assert len(within) == 1
    assert "high uncertainty" in within[0].lower()


def test_format_gate_rationales_handles_empty_snapshot() -> None:
    """Test format_gate_rationales with empty or invalid snapshots."""
    assert format_gate_rationales({}) == []
    assert format_gate_rationales({"rationales": "not_a_dict"}) == []
    assert format_gate_rationales({"rationales": {}}) == []


def test_audit_status_rollup_handles_empty_audits() -> None:
    """Test audit_status_rollup with empty audit list."""
    counts = audit_status_rollup([])
    assert counts == {}


def test_audit_status_rollup_handles_unknown_statuses() -> None:
    """Test audit_status_rollup with unknown statuses."""
    from typing import Mapping, Any
    audits: list[Mapping[str, Any]] = [
        {"status": "supported"},
        {"status": "unknown_status"},
        {"status": "needs_review"},
        {"status": "another_unknown"},
    ]
    counts = audit_status_rollup(audits)
    assert counts["supported"] == 1
    assert counts["needs_review"] == 1
    assert "unknown_status" in counts
    assert "another_unknown" in counts
