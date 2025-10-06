# mypy: ignore-errors
import pytest
from unittest.mock import patch
from autoresearch.config.models import ConfigModel
from autoresearch.search import Search


def test_cross_backend_rank_combines_results():
    results = {
        "a": [{"title": "A", "url": "a"}],
        "b": [{"title": "B", "url": "b"}],
    }
    cfg = ConfigModel()
    cfg.search.use_semantic_similarity = False
    with patch("autoresearch.search.core.get_config", return_value=cfg):
        ranked = Search.cross_backend_rank("q", results)
    urls = [r["url"] for r in ranked]
    assert set(urls) == {"a", "b"}


def test_rank_results_weight_sum_error():
    cfg = ConfigModel()
    cfg.search.semantic_similarity_weight = 0.6
    cfg.search.bm25_weight = 0.6
    cfg.search.source_credibility_weight = 0.0
    with patch("autoresearch.search.core.get_config", return_value=cfg):
        with pytest.raises(Exception):
            Search.rank_results("q", [{"title": "t", "url": "u"}])
