"""Unit tests for the enhanced relevance ranking functionality in the search module.

This module tests the BM25 algorithm, semantic similarity scoring, source credibility
assessment, and the overall ranking functionality.
"""

import pytest
from unittest.mock import patch, MagicMock
import numpy as np

from autoresearch.search import Search
from autoresearch.config import SearchConfig


@pytest.fixture
def mock_config():
    """Create a mock configuration for testing."""
    search_config = SearchConfig(
        use_bm25=True,
        use_semantic_similarity=True,
        use_source_credibility=True,
        bm25_weight=0.3,
        semantic_similarity_weight=0.5,
        source_credibility_weight=0.2,
    )
    config = MagicMock()
    config.search = search_config
    return config


@pytest.fixture
def sample_results():
    """Create sample search results for testing."""
    return [
        {
            "title": "Python Programming",
            "url": "https://python.org",
            "snippet": "Official Python website",
        },
        {
            "title": "Learn Python",
            "url": "https://example.com/python",
            "snippet": "Python tutorials",
        },
        {
            "title": "Python (programming language) - Wikipedia",
            "url": "https://en.wikipedia.org/wiki/Python_(programming_language)",
            "snippet": "Python is a high-level programming language",
        },
        {
            "title": "Unrelated Result",
            "url": "https://example.com/unrelated",
            "snippet": "Something completely different",
        },
    ]


def test_preprocess_text():
    """Test the text preprocessing functionality."""
    text = "Python 3.9 is GREAT! It has many new features."
    tokens = Search.preprocess_text(text)

    # Check that tokens are lowercase
    assert all(t == t.lower() for t in tokens)

    # Check that numbers are removed
    assert "3.9" not in tokens

    # Check that punctuation is removed
    assert "!" not in tokens
    assert "." not in tokens

    # Check that expected tokens are present
    assert "python" in tokens
    assert "great" in tokens
    assert "features" in tokens


@patch("autoresearch.search.BM25_AVAILABLE", True)
@patch("autoresearch.search.BM25Okapi")
def test_calculate_bm25_scores(mock_bm25, sample_results):
    """Test the BM25 scoring functionality."""
    # Setup mock BM25 model
    mock_bm25_instance = MagicMock()
    mock_bm25_instance.get_scores.return_value = np.array([0.8, 0.6, 0.9, 0.1])
    mock_bm25.return_value = mock_bm25_instance

    # Calculate BM25 scores
    scores = Search.calculate_bm25_scores("python programming", sample_results)

    # Check that scores are normalized to [0, 1]
    assert all(0 <= score <= 1 for score in scores)

    # Check that the highest score is 1.0 (after normalization)
    assert max(scores) == 1.0

    # Check that the scores are in the expected order
    assert scores[2] > scores[0] > scores[1] > scores[3]


@patch("autoresearch.search.SENTENCE_TRANSFORMERS_AVAILABLE", True)
def test_calculate_semantic_similarity(sample_results):
    """Test the semantic similarity scoring functionality."""
    # Create a mock sentence transformer
    mock_transformer = MagicMock()

    # Mock the encode method to return embeddings
    def mock_encode(texts):
        if isinstance(texts, str):
            # Query embedding
            return np.array([0.1, 0.2, 0.3])
        else:
            # Document embeddings
            return np.array(
                [
                    [0.1, 0.2, 0.3],  # Similar to query
                    [0.2, 0.3, 0.4],  # Somewhat similar
                    [0.1, 0.2, 0.3],  # Similar to query
                    [-0.1, -0.2, -0.3],  # Opposite direction (negative similarity)
                ]
            )

    mock_transformer.encode = mock_encode

    # Patch the get_sentence_transformer method
    with patch.object(
        Search, "get_sentence_transformer", return_value=mock_transformer
    ):
        scores = Search.calculate_semantic_similarity(
            "python programming", sample_results
        )

    # Check that scores are in the expected range
    assert all(-1 <= score <= 1 for score in scores)

    # Check that similar documents have higher scores
    assert scores[0] > 0.9  # Very similar
    assert scores[2] > 0.9  # Very similar
    assert 0 < scores[1] < 1  # Somewhat similar
    assert scores[3] < 0  # Negative similarity


def test_assess_source_credibility(sample_results):
    """Test the source credibility assessment functionality."""
    scores = Search.assess_source_credibility(sample_results)

    # Check that all scores are in the [0, 1] range
    assert all(0 <= score <= 1 for score in scores)

    # Check that Wikipedia has a high credibility score
    wikipedia_index = next(
        i for i, r in enumerate(sample_results) if "wikipedia.org" in r["url"]
    )
    assert scores[wikipedia_index] > 0.8

    # Check that python.org has a good credibility score
    python_index = next(
        i for i, r in enumerate(sample_results) if "python.org" in r["url"]
    )
    assert scores[python_index] >= 0.5

    # Check that unknown domains have a default score
    unknown_index = next(
        i for i, r in enumerate(sample_results) if "example.com" in r["url"]
    )
    assert scores[unknown_index] == 0.5


@patch("autoresearch.search.get_config")
def test_rank_results(mock_get_config, mock_config, sample_results):
    """Test the overall ranking functionality."""
    mock_get_config.return_value = mock_config

    # Mock the scoring methods to return predictable scores
    with (
        patch.object(
            Search, "calculate_bm25_scores", return_value=[0.8, 0.6, 0.9, 0.1]
        ),
        patch.object(
            Search, "calculate_semantic_similarity", return_value=[0.7, 0.5, 0.9, 0.1]
        ),
        patch.object(
            Search, "assess_source_credibility", return_value=[0.7, 0.5, 0.9, 0.5]
        ),
    ):
        ranked_results = Search.rank_results("python programming", sample_results)

    # Check that results are ranked in the expected order
    assert (
        ranked_results[0]["url"]
        == "https://en.wikipedia.org/wiki/Python_(programming_language)"
    )  # Highest overall score
    assert ranked_results[1]["url"] == "https://python.org"  # Second highest
    assert ranked_results[2]["url"] == "https://example.com/python"  # Third
    assert ranked_results[3]["url"] == "https://example.com/unrelated"  # Lowest

    # Check that scores are added to the results
    assert "relevance_score" in ranked_results[0]
    assert "bm25_score" in ranked_results[0]
    assert "semantic_score" in ranked_results[0]
    assert "credibility_score" in ranked_results[0]


@patch("autoresearch.search.get_config")
def test_rank_results_with_disabled_features(
    mock_get_config, mock_config, sample_results
):
    """Test ranking with some features disabled."""
    # Disable BM25 and source credibility
    mock_config.search.use_bm25 = False
    mock_config.search.use_source_credibility = False
    mock_get_config.return_value = mock_config

    # Mock the semantic similarity method to return predictable scores
    with patch.object(
        Search, "calculate_semantic_similarity", return_value=[0.7, 0.5, 0.9, 0.1]
    ):
        ranked_results = Search.rank_results("python programming", sample_results)

    # Check that results are ranked based only on semantic similarity
    assert (
        ranked_results[0]["url"]
        == "https://en.wikipedia.org/wiki/Python_(programming_language)"
    )  # Highest semantic score
    assert ranked_results[1]["url"] == "https://python.org"  # Second highest
    assert ranked_results[2]["url"] == "https://example.com/python"  # Third
    assert ranked_results[3]["url"] == "https://example.com/unrelated"  # Lowest

    # Check that disabled scores are neutral (1.0)
    assert ranked_results[0]["bm25_score"] == 1.0
    assert ranked_results[0]["credibility_score"] == 1.0


@patch("autoresearch.search.get_config")
@patch("autoresearch.search.BM25_AVAILABLE", False)
@patch("autoresearch.search.SENTENCE_TRANSFORMERS_AVAILABLE", False)
def test_rank_results_with_unavailable_libraries(
    mock_get_config, mock_config, sample_results
):
    """Test ranking when required libraries are not available."""
    mock_get_config.return_value = mock_config

    # Even with libraries unavailable, ranking should still work
    ranked_results = Search.rank_results("python programming", sample_results)

    # Check that we got results back
    assert len(ranked_results) == len(sample_results)

    # Check that all scores are neutral (1.0) for unavailable features
    assert all(result["bm25_score"] == 1.0 for result in ranked_results)
    assert all(result["semantic_score"] == 1.0 for result in ranked_results)
