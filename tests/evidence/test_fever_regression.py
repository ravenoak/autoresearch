"""Regression tests for claim evidence utilities."""

from __future__ import annotations

from dataclasses import dataclass

from autoresearch.agents.mixins import ClaimGeneratorMixin
from autoresearch.evidence import (
    classify_entailment,
    expand_retrieval_queries,
    score_entailment,
)
from autoresearch.storage import ClaimAuditRecord, ClaimAuditStatus


@dataclass
class _MixinHarness(ClaimGeneratorMixin):
    """Minimal harness to expose mixin behaviour in tests."""


def test_expand_retrieval_queries_generates_contextual_variations() -> None:
    claim = "The Eiffel Tower is located in Paris."
    expansions = expand_retrieval_queries(
        claim, base_query="France landmarks", max_variations=4
    )
    assert expansions
    assert expansions[0] == claim
    assert any("supporting" in variant for variant in expansions)


def test_entailment_scoring_supported_claim() -> None:
    claim = "The Eiffel Tower is in Paris."
    evidence = "Paris is home to the famous Eiffel Tower landmark."
    breakdown = score_entailment(claim, evidence)
    assert breakdown.score > 0.6
    status = classify_entailment(breakdown.score)
    assert status == ClaimAuditStatus.SUPPORTED
    record = ClaimAuditRecord(
        claim_id="claim-1",
        status=status,
        entailment_score=breakdown.score,
        sources=[{"snippet": evidence}],
    )
    payload = record.to_payload()
    recovered = ClaimAuditRecord.from_payload(payload)
    assert recovered.status == status
    assert recovered.entailment_score == record.entailment_score


def test_entailment_scoring_unsupported_claim() -> None:
    claim = "The Eiffel Tower is in Paris."
    evidence = "The Statue of Liberty stands in New York Harbor."
    breakdown = score_entailment(claim, evidence)
    assert breakdown.score < 0.3
    status = classify_entailment(breakdown.score)
    assert status == ClaimAuditStatus.UNSUPPORTED


def test_claim_audit_record_from_score_overrides_status() -> None:
    record = ClaimAuditRecord.from_score(
        "claim-override",
        0.15,
        status="needs_review",
        sources=[{"title": "Manual review"}],
    )
    assert record.status is ClaimAuditStatus.NEEDS_REVIEW
    assert record.sources[0]["title"] == "Manual review"


def test_claim_generator_attaches_audit_metadata() -> None:
    harness = _MixinHarness()
    record = ClaimAuditRecord(
        claim_id="placeholder",
        status=ClaimAuditStatus.NEEDS_REVIEW,
        entailment_score=0.4,
    )
    claim = harness.create_claim(
        "Paris hosts the Eiffel Tower.",
        "thesis",
        audit=record,
    )
    assert "audit" in claim
    assert claim["audit"]["claim_id"] == claim["id"]
    assert claim["audit"]["status"] == ClaimAuditStatus.NEEDS_REVIEW.value

    claim2 = harness.create_claim(
        "The Louvre is in Paris.",
        "thesis",
        verification_status="supported",
        verification_sources=[{"title": "Museums in Paris"}],
        entailment_score=0.72,
    )
    assert claim2["audit"]["status"] == ClaimAuditStatus.SUPPORTED.value
    assert claim2["audit"]["entailment_score"] == 0.72
    assert claim2["audit"]["sources"][0]["title"] == "Museums in Paris"
