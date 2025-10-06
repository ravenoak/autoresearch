# mypy: ignore-errors
from typing import Mapping, Sequence

from unittest.mock import patch

import pytest

from autoresearch.config.models import ConfigModel, SearchConfig
from autoresearch.search import Search


SearchResults = Sequence[Mapping[str, object]]


def test_convex_combination_matches_docs(monkeypatch: pytest.MonkeyPatch) -> None:
    search_cfg = SearchConfig.model_construct(
        semantic_similarity_weight=0.2,
        bm25_weight=0.6,
        source_credibility_weight=0.2,
    )
    cfg = ConfigModel.model_construct(search=search_cfg)
    cfg.api.role_permissions["anonymous"] = ["query"]

    def get_config_override() -> ConfigModel:
        return cfg

    monkeypatch.setattr("autoresearch.search.core.get_config", get_config_override)

    bm25: list[float] = [0.7, 0.2]

    def _bm25_scores(
        _: str, __: Sequence[Mapping[str, object]]
    ) -> list[float]:  # pragma: no cover - deterministic stub
        return bm25
    semantic: list[float] = [0.4, 0.9]
    cred: list[float] = [0.5, 0.1]
    docs: list[Mapping[str, object]] = [
        {"id": 0, "similarity": semantic[0]},
        {"id": 1, "similarity": semantic[1]},
    ]

    with (
        patch.object(Search, "calculate_bm25_scores", staticmethod(_bm25_scores)),
        patch.object(
            Search, "calculate_semantic_similarity", return_value=semantic
        ),
        patch.object(Search, "assess_source_credibility", return_value=cred),
    ):
        ranked: SearchResults = Search.rank_results("q", docs)

    w_s = search_cfg.semantic_similarity_weight
    w_b = search_cfg.bm25_weight
    w_c = search_cfg.source_credibility_weight
    bm25_min, bm25_max = min(bm25), max(bm25)
    bm25_norm = [0.0 if bm25_max == bm25_min else (b - bm25_min) / (bm25_max - bm25_min) for b in bm25]
    sem_min, sem_max = min(semantic), max(semantic)
    sem_norm = [0.0 if sem_max == sem_min else (s - sem_min) / (sem_max - sem_min) for s in semantic]
    cred_min, cred_max = min(cred), max(cred)
    cred_norm = [0.0 if cred_max == cred_min else (c - cred_min) / (cred_max - cred_min) for c in cred]
    expected = [
        w_b * bm25_norm[i] + w_s * sem_norm[i] + w_c * cred_norm[i]
        for i in range(2)
    ]
    exp_min, exp_max = min(expected), max(expected)
    normalized = [
        0.0 if exp_max == exp_min else (e - exp_min) / (exp_max - exp_min)
        for e in expected
    ]

    ranked_ids = [r["id"] for r in ranked]
    expected_ids = [i for i, _ in sorted(enumerate(normalized), key=lambda p: p[1], reverse=True)]
    assert ranked_ids == expected_ids

    for r in ranked:
        idx = r["id"]
        assert r["relevance_score"] == pytest.approx(normalized[idx])
