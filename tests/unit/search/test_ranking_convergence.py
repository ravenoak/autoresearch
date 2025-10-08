# mypy: ignore-errors
"""Tests for ranking convergence simulation."""

import pytest

from autoresearch.search.ranking_convergence import (
    DocScores,
    relevance_scores,
    simulate_ranking_convergence,
)


class TestDocScores:
    """Tests for DocScores dataclass."""

    def test_doc_scores_creation(self):
        """Test DocScores can be created with valid values."""
        scores = DocScores(bm25=0.8, semantic=0.6, credibility=0.9)
        assert scores.bm25 == 0.8
        assert scores.semantic == 0.6
        assert scores.credibility == 0.9

    def test_doc_scores_frozen(self):
        """Test DocScores is frozen (immutable)."""
        scores = DocScores(bm25=0.5, semantic=0.7, credibility=0.8)
        with pytest.raises(AttributeError):
            scores.bm25 = 0.9


class TestRelevanceScores:
    """Tests for relevance_scores function."""

    def test_relevance_scores_basic(self):
        """Test relevance_scores with basic inputs."""
        docs = [
            DocScores(bm25=0.8, semantic=0.6, credibility=0.7),
            DocScores(bm25=0.5, semantic=0.9, credibility=0.8),
        ]
        weights = [0.4, 0.4, 0.2]
        scores = relevance_scores(docs, weights)
        assert len(scores) == 2
        assert all(isinstance(s, float) for s in scores)
        assert all(0.0 <= s <= 1.0 for s in scores)

    def test_relevance_scores_equal_weights(self):
        """Test relevance_scores with equal weights."""
        docs = [
            DocScores(bm25=1.0, semantic=0.0, credibility=0.0),
            DocScores(bm25=0.0, semantic=1.0, credibility=0.0),
            DocScores(bm25=0.0, semantic=0.0, credibility=1.0),
        ]
        weights = [1/3, 1/3, 1/3]
        scores = relevance_scores(docs, weights)
        assert len(scores) == 3
        # All should be equal since weights are equal and each doc has one perfect score
        assert scores[0] == pytest.approx(scores[1], abs=0.01)
        assert scores[1] == pytest.approx(scores[2], abs=0.01)


class TestSimulateRankingConvergence:
    """Tests for simulate_ranking_convergence function."""

    def test_simulate_convergence_basic(self):
        """Test basic convergence simulation."""
        docs = [
            DocScores(bm25=0.8, semantic=0.6, credibility=0.7),
            DocScores(bm25=0.5, semantic=0.9, credibility=0.8),
            DocScores(bm25=0.3, semantic=0.4, credibility=0.9),
        ]
        weights = [0.4, 0.4, 0.2]
        orderings = simulate_ranking_convergence(docs, weights, iterations=2)
        assert len(orderings) == 2
        assert all(len(ordering) == 3 for ordering in orderings)
        # Each ordering should be a permutation of [0, 1, 2]
        for ordering in orderings:
            assert sorted(ordering) == [0, 1, 2]

    def test_simulate_convergence_single_iteration(self):
        """Test convergence simulation with single iteration."""
        docs = [
            DocScores(bm25=0.5, semantic=0.7, credibility=0.6),
            DocScores(bm25=0.8, semantic=0.4, credibility=0.9),
        ]
        weights = [0.3, 0.3, 0.4]
        orderings = simulate_ranking_convergence(docs, weights, iterations=1)
        assert len(orderings) == 1
        assert len(orderings[0]) == 2

    def test_simulate_convergence_no_iterations(self):
        """Test convergence simulation with zero iterations."""
        docs = [
            DocScores(bm25=0.5, semantic=0.7, credibility=0.6),
        ]
        weights = [0.3, 0.3, 0.4]
        orderings = simulate_ranking_convergence(docs, weights, iterations=0)
        assert len(orderings) == 0
