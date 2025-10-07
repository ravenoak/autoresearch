# mypy: ignore-errors
"""Unit tests for the enhanced relevance ranking functionality in the search module.

This module tests the BM25 algorithm, semantic similarity scoring, source credibility
assessment, and the overall ranking functionality.
"""

import os
from tempfile import TemporaryDirectory
from unittest.mock import MagicMock, patch

import numpy as np
import pytest
from hypothesis import HealthCheck, given, settings, strategies as st

from autoresearch.cache import SearchCache
from autoresearch.config.models import (
    AdaptiveKConfig,
    ContextAwareSearchConfig,
    QueryRewriteConfig,
    SearchConfig,
)
from autoresearch.errors import ConfigError
from autoresearch.search import Search
from autoresearch.search.core import RANKING_BUCKET_SCALE


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


@patch("autoresearch.search.core.BM25_AVAILABLE", True)
@patch("autoresearch.search.core.BM25Okapi")
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


def test_rank_results_empty_input(monkeypatch):
    monkeypatch.setattr("autoresearch.search.core.BM25_AVAILABLE", True)
    assert Search.rank_results("q", []) == []


@patch("autoresearch.search.SENTENCE_TRANSFORMERS_AVAILABLE", True)
def test_calculate_semantic_similarity(sample_results):
    """Semantic scores follow the cosine spec and documented coverage.

    The regression links the production path to
    ``docs/algorithms/semantic_similarity.md`` and ``SPEC_COVERAGE.md`` by
    checking the normalized cosine similarity values.
    """
    # Create a mock sentence transformer
    mock_transformer = MagicMock()

    # Mock the embed method to return embeddings
    def mock_embed(texts):
        if isinstance(texts, str):
            texts = [texts]
        if len(texts) == 1:
            return [np.array([0.1, 0.2, 0.3], dtype=float)]
        return [
            np.array([0.1, 0.2, 0.3], dtype=float),
            np.array([0.2, 0.3, 0.4], dtype=float),
            np.array([0.1, 0.2, 0.3], dtype=float),
            np.array([-0.1, -0.2, -0.3], dtype=float),
        ]

    mock_transformer.embed = mock_embed
    mock_transformer.encode = mock_embed

    # Patch the get_sentence_transformer method
    with patch.object(
        Search, "get_sentence_transformer", return_value=mock_transformer
    ):
        scores = Search.calculate_semantic_similarity(
            "python programming", sample_results
        )

    # Check that scores are in the expected range
    assert all(0 <= score <= 1 for score in scores)

    query_vec = np.array([0.1, 0.2, 0.3], dtype=float)
    doc_vectors = [
        np.array([0.1, 0.2, 0.3], dtype=float),
        np.array([0.2, 0.3, 0.4], dtype=float),
        np.array([0.1, 0.2, 0.3], dtype=float),
        np.array([-0.1, -0.2, -0.3], dtype=float),
    ]
    expected = []
    for vector in doc_vectors:
        numerator = float(np.dot(query_vec, vector))
        denominator = float(np.linalg.norm(query_vec) * np.linalg.norm(vector))
        cosine = numerator / denominator
        expected.append((cosine + 1) / 2)

    assert scores == pytest.approx(expected)
    assert scores[0] == pytest.approx(1.0)
    assert scores[0] > scores[1]
    assert scores[3] == pytest.approx(0.0, abs=1e-9)


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


@patch("autoresearch.search.core.get_config")
def test_rank_results(mock_get_config, mock_config, sample_results):
    """Test the overall ranking functionality."""
    mock_get_config.return_value = mock_config

    # Mock the scoring methods to return predictable scores
    with (
        patch.object(
            Search,
            "calculate_bm25_scores",
            staticmethod(lambda q, d: [0.8, 0.6, 0.9, 0.1]),
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


@patch("autoresearch.search.core.get_config")
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


@patch("autoresearch.search.core.get_config")
@patch("autoresearch.search.core.BM25_AVAILABLE", False)
@patch("autoresearch.search.core.SENTENCE_TRANSFORMERS_AVAILABLE", False)
@patch(
    "autoresearch.search.core._try_import_sentence_transformers", return_value=False
)
def test_rank_results_with_unavailable_libraries(
    _mock_try_import, mock_get_config, mock_config, sample_results
):
    """Test ranking when required libraries are not available."""
    mock_get_config.return_value = mock_config

    # Even with libraries unavailable, ranking should still work
    ranked_results = Search.rank_results("python programming", sample_results)

    # Check that we got results back
    assert len(ranked_results) == len(sample_results)

    # Check that all scores are neutral for unavailable features
    assert all(result["bm25_score"] == 1.0 for result in ranked_results)
    assert all(result["semantic_score"] == 0.5 for result in ranked_results)


@patch("autoresearch.search.core.get_config")
def test_rank_results_weighted_combination(mock_get_config, mock_config, sample_results):
    """Ranking should respect configured weights for keyword and semantic scores."""
    mock_config.search.semantic_similarity_weight = 0.8
    mock_config.search.bm25_weight = 0.2
    mock_config.search.source_credibility_weight = 0.0
    mock_get_config.return_value = mock_config

    with (
        patch.object(
            Search,
            "calculate_bm25_scores",
            staticmethod(lambda q, d: [0.1, 0.9, 0.1, 0.1]),
        ),
        patch.object(Search, "calculate_semantic_similarity", return_value=[0.9, 0.1, 0.2, 0.3]),
        patch.object(Search, "assess_source_credibility", return_value=[1.0]*4),
    ):
        ranked_results = Search.rank_results("test query", sample_results)

    # Semantic score weight dominates so first result should be index 0
    assert ranked_results[0]["url"] == "https://python.org"


@patch("autoresearch.search.core.get_config")
def test_rank_results_bm25_only(mock_get_config, mock_config, sample_results):
    """Ranking should rely solely on BM25 when other weights are zero."""
    mock_config.search.bm25_weight = 1.0
    mock_config.search.semantic_similarity_weight = 0.0
    mock_config.search.source_credibility_weight = 0.0
    mock_get_config.return_value = mock_config

    with (
        patch.object(
            Search,
            "calculate_bm25_scores",
            staticmethod(lambda q, d: [0.2, 0.4, 0.1, 0.9]),
        ),
        patch.object(Search, "calculate_semantic_similarity", return_value=[0.5] * 4),
        patch.object(Search, "assess_source_credibility", return_value=[0.6] * 4),
    ):
        ranked_results = Search.rank_results("test query", sample_results)

    assert ranked_results[0]["url"] == "https://example.com/unrelated"


@patch("autoresearch.search.core.get_config")
def test_rank_results_patched_bm25_function(
    mock_get_config, mock_config, sample_results
):
    """`rank_results` should pass both query and documents to BM25 scorer."""
    mock_config.search.bm25_weight = 1.0
    mock_config.search.semantic_similarity_weight = 0.0
    mock_config.search.source_credibility_weight = 0.0
    mock_get_config.return_value = mock_config

    captured: dict[str, object] = {}

    def fake_bm25(query: str, documents: list[dict[str, object]]) -> list[float]:
        captured["query"] = query
        captured["documents"] = documents
        return [0.1] * len(documents)

    with patch.object(
        Search,
        "calculate_bm25_scores",
        staticmethod(fake_bm25),
    ):
        ranked = Search.rank_results("q", sample_results)

    assert captured["query"] == "q"
    assert captured["documents"] is sample_results
    assert len(ranked) == len(sample_results)


def test_search_config_invalid_weights():
    """Invalid weight combinations should raise ConfigError."""
    with pytest.raises(ConfigError):
        SearchConfig(
            bm25_weight=0.5,
            semantic_similarity_weight=0.3,
            source_credibility_weight=0.5,
        )


@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(data=st.data())
def test_rank_results_sorted(mock_config, data):
    """Ranking must return results sorted by relevance_score."""
    n = data.draw(st.integers(min_value=1, max_value=5))
    results = [
        {
            "title": f"title {i}",
            "url": f"https://example.com/{i}",
            "snippet": "s",
        }
        for i in range(n)
    ]
    bm25 = data.draw(
        st.lists(st.floats(min_value=0, max_value=1), min_size=n, max_size=n)
    )
    semantic = data.draw(
        st.lists(st.floats(min_value=0, max_value=1), min_size=n, max_size=n)
    )
    credibility = data.draw(
        st.lists(st.floats(min_value=0, max_value=1), min_size=n, max_size=n)
    )
    with (
        patch("autoresearch.search.core.get_config", return_value=mock_config),
        patch.object(
            Search,
            "calculate_bm25_scores",
            staticmethod(lambda q, d: bm25),
        ),
        patch.object(Search, "calculate_semantic_similarity", return_value=semantic),
        patch.object(Search, "assess_source_credibility", return_value=credibility),
    ):
        ranked = Search.rank_results("q", results)

    assert len(ranked) == n
    buckets = [item["relevance_bucket"] for item in ranked]
    assert all(buckets[i] >= buckets[i + 1] for i in range(len(buckets) - 1))
    tolerance = 1.0 / RANKING_BUCKET_SCALE
    for i in range(len(ranked) - 1):
        if buckets[i] == buckets[i + 1]:
            assert ranked[i]["relevance_score"] >= ranked[i + 1]["relevance_score"] - tolerance
        else:
            assert ranked[i]["relevance_score"] >= ranked[i + 1]["relevance_score"]


@settings(deadline=None, max_examples=10)
@given(
    texts=st.lists(st.text(min_size=1), min_size=1, max_size=5),
    namespace=st.sampled_from([None, "team-alpha"]),
)
def test_external_lookup_uses_cache(texts, namespace):
    """External lookups reuse cached results per the cache documentation.

    Coverage traces to ``docs/algorithms/cache.md`` and ``SPEC_COVERAGE.md``.
    """
    results = [
        {"title": t, "url": f"https://example.com/{i}", "snippet": "s"}
        for i, t in enumerate(texts)
    ]
    backend = MagicMock(return_value=results)
    raw_query = "  Mixed Case Query  "

    with TemporaryDirectory() as tmpdir:
        cache = SearchCache(db_path=os.path.join(tmpdir, "cache.json"))
        cfg = MagicMock()
        cfg.search = SearchConfig(
            backends=["mock"],
            embedding_backends=[],
            use_bm25=False,
            use_semantic_similarity=False,
            use_source_credibility=False,
            bm25_weight=0.0,
            semantic_similarity_weight=0.0,
            source_credibility_weight=1.0,
            context_aware=ContextAwareSearchConfig(enabled=False),
            query_rewrite=QueryRewriteConfig(enabled=False),
            adaptive_k=AdaptiveKConfig(enabled=False),
            cache_namespace=namespace,
        )

        with patch("autoresearch.search.core.get_config", return_value=cfg):
            search = Search(cache=cache)
            search.backends = {"mock": backend}

            bundle = search.external_lookup(raw_query, max_results=3, return_handles=True)
            canonical_payload = {
                "text": raw_query,
                "raw_query": bundle.raw_query,
                "executed_query": bundle.executed_query,
                "canonical_query": bundle.query,
                "raw_canonical_query": bundle.raw_canonical_query,
            }
            second = search.external_lookup(canonical_payload, max_results=3)

    assert backend.call_count == 1
    assert list(bundle) == bundle.results
    assert second == bundle.results


@patch("autoresearch.search.core.get_config")
def test_relevance_score_monotonic(mock_get_config, mock_config):
    """Increasing a component score should raise the final relevance score."""
    docs1 = [
        {"title": "a", "url": "https://a", "snippet": ""},
        {"title": "b", "url": "https://b", "snippet": ""},
    ]
    docs2 = [
        {"title": "a", "url": "https://a", "snippet": ""},
        {"title": "b", "url": "https://b", "snippet": ""},
    ]
    mock_get_config.return_value = mock_config
    with (
        patch.object(Search, "calculate_semantic_similarity", return_value=[0.5, 0.5]),
        patch.object(Search, "assess_source_credibility", return_value=[0.5, 0.5]),
    ):
        with patch.object(
            Search,
            "calculate_bm25_scores",
            staticmethod(lambda q, d: [0.2, 0.4]),
        ):
            before_rank = Search.rank_results("q", docs1)
            before = {r["url"]: r["relevance_score"] for r in before_rank}["https://a"]
        with patch.object(
            Search,
            "calculate_bm25_scores",
            staticmethod(lambda q, d: [0.8, 0.4]),
        ):
            after_rank = Search.rank_results("q", docs2)
            after = {r["url"]: r["relevance_score"] for r in after_rank}["https://a"]

    assert after > before
    assert after_rank[0]["url"] == "https://a"


@patch("autoresearch.search.core.get_config")
def test_weight_sensitivity(mock_get_config, mock_config):
    """Adjusting weights should reorder results to match their emphasis."""
    docs = [
        {"title": "a", "url": "https://a", "snippet": ""},
        {"title": "b", "url": "https://b", "snippet": ""},
    ]
    with (
        patch.object(Search, "calculate_bm25_scores", return_value=[0.9, 0.1]),
        patch.object(Search, "calculate_semantic_similarity", return_value=[0.1, 0.9]),
        patch.object(Search, "assess_source_credibility", return_value=[0.5, 0.5]),
    ):
        mock_config.search.bm25_weight = 0.7
        mock_config.search.semantic_similarity_weight = 0.2
        mock_config.search.source_credibility_weight = 0.1
        mock_get_config.return_value = mock_config
        ranked_bm25 = Search.rank_results("q", docs)

        mock_config.search.bm25_weight = 0.2
        mock_config.search.semantic_similarity_weight = 0.7
        mock_config.search.source_credibility_weight = 0.1
        ranked_sem = Search.rank_results("q", docs)

    assert ranked_bm25[0]["url"] == "https://a"
    assert ranked_sem[0]["url"] == "https://b"
