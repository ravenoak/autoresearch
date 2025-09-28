"""Unit tests for evidence stability utilities."""

import pytest

from autoresearch.evidence import (
    aggregate_entailment_scores,
    sample_paraphrases,
)


def test_aggregate_entailment_scores_stable() -> None:
    """Consistent scores should yield a stable aggregate."""

    aggregate = aggregate_entailment_scores([0.7, 0.72, 0.68])
    assert aggregate.sample_size == 3
    assert aggregate.disagreement is False
    assert aggregate.mean == pytest.approx(0.7, abs=1e-2)
    assert aggregate.variance < 0.005


def test_aggregate_entailment_scores_unstable() -> None:
    """Divergent scores should trigger the disagreement flag."""

    aggregate = aggregate_entailment_scores([0.1, 0.9])
    assert aggregate.sample_size == 2
    assert aggregate.disagreement is True
    assert aggregate.variance > 0.25


def test_sample_paraphrases_returns_unique_variants() -> None:
    """Paraphrase sampler should provide diverse, normalised variants."""

    variants = sample_paraphrases("Vaccines reduce hospitalisations.", max_samples=4)
    assert variants  # at least one variant
    assert len(set(variant.lower() for variant in variants)) == len(variants)
    assert any(variant.endswith("?") for variant in variants)
