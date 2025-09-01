"""Tests for dataset ranking comparison simulation."""

from scripts.ranking_dataset_comparison import compare_datasets


def test_low_noise_outperforms_high_noise() -> None:
    """Datasets with less noise should yield higher NDCG."""

    scores = compare_datasets([0.0, 0.3])
    assert scores["noise-0.0"] > scores["noise-0.3"]
