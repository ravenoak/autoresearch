import math

from autoresearch.config.models import NamespaceMergeConfig, NamespaceMergeStrategy
from autoresearch.storage import StorageManager


def _index_by_id(records):
    return {record["id"]: record for record in records}


def test_merge_claim_groups_union_selects_highest_confidence():
    claims = {
        "alpha": [
            {"id": "c1", "confidence": 0.4, "content": "alpha"},
            {"id": "c2", "confidence": 0.9},
        ],
        "beta": [
            {"id": "c1", "confidence": 0.6, "notes": "beta"},
        ],
    }

    merged = StorageManager.merge_claim_groups(claims)

    merged_by_id = _index_by_id(merged)
    assert len(merged_by_id) == 2
    c1 = merged_by_id["c1"]
    assert math.isclose(c1["confidence"], 0.6)
    assert set(c1["namespaces"]) == {"alpha", "beta"}
    assert c1["notes"] == "beta"
    c2 = merged_by_id["c2"]
    assert c2["namespaces"] == ["alpha"]


def test_merge_claim_groups_confidence_weighted_average():
    claims = {
        "alpha": [
            {"id": "c1", "confidence": 0.2},
        ],
        "beta": [
            {"id": "c1", "confidence": 0.8},
        ],
    }
    policy = NamespaceMergeConfig(
        strategy=NamespaceMergeStrategy.CONFIDENCE_WEIGHT,
        weights={"alpha": 2.0, "beta": 1.0},
    )

    merged = StorageManager.merge_claim_groups(claims, policy)

    assert len(merged) == 1
    entry = merged[0]
    expected = (0.2 * 2.0 + 0.8 * 1.0) / 3.0
    assert math.isclose(entry["confidence"], expected)
    assert set(entry["namespaces"]) == {"alpha", "beta"}
