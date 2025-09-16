# Config Weight Sum Simulation

## Purpose

This note documents a reproducible simulation verifying the invariants cited by
[config specification](../specs/config.md).

## Method

We executed `uv run python` with the script below to instantiate `SearchConfig`
and `ConfigModel` variants. The script inspects ranking weight normalization,
token budget validation, and eviction policy canonicalisation.

### Script

```python
from __future__ import annotations

import json

from autoresearch.config.models import ConfigModel, SearchConfig
from autoresearch.errors import ConfigError

weights: dict[str, object] = {}
default = SearchConfig()
weights["default"] = {
    "sum": round(
        default.semantic_similarity_weight
        + default.bm25_weight
        + default.source_credibility_weight,
        6,
    ),
    "weights": {
        "semantic": default.semantic_similarity_weight,
        "bm25": default.bm25_weight,
        "source": default.source_credibility_weight,
    },
}
partial = SearchConfig(semantic_similarity_weight=0.6, bm25_weight=0.2)
weights["partial_override"] = {
    "sum": round(
        partial.semantic_similarity_weight
        + partial.bm25_weight
        + partial.source_credibility_weight,
        6,
    ),
    "weights": {
        "semantic": partial.semantic_similarity_weight,
        "bm25": partial.bm25_weight,
        "source": partial.source_credibility_weight,
    },
}
try:
    SearchConfig(semantic_similarity_weight=0.9, bm25_weight=0.3)
except ConfigError:
    weights["overweight_guard"] = "ConfigError raised"
else:
    weights["overweight_guard"] = "missing error"
zeros = SearchConfig(
    semantic_similarity_weight=0.0,
    bm25_weight=0.0,
    source_credibility_weight=0.0,
)
weights["zero_rebalanced"] = {
    "sum": round(
        zeros.semantic_similarity_weight
        + zeros.bm25_weight
        + zeros.source_credibility_weight,
        6,
    ),
    "weights": {
        "semantic": zeros.semantic_similarity_weight,
        "bm25": zeros.bm25_weight,
        "source": zeros.source_credibility_weight,
    },
}

budgets: dict[str, object] = {}
model = ConfigModel(token_budget=1024)
budgets["positive_int"] = model.token_budget
model = ConfigModel(token_budget="2048")
budgets["numeric_string"] = model.token_budget
for value in [0, -1, "-16"]:
    try:
        ConfigModel(token_budget=value)
    except ConfigError:
        budgets[f"invalid_{value}"] = "ConfigError raised"
    else:
        budgets[f"invalid_{value}"] = "missing error"

policies = {
    "score_normalized": ConfigModel(
        graph_eviction_policy="score",
    ).graph_eviction_policy,
    "lru_casefold": ConfigModel(
        graph_eviction_policy="lRu",
    ).graph_eviction_policy,
}

print(
    json.dumps(
        {
            "ranking_weights": weights,
            "token_budget": budgets,
            "eviction_policy": policies,
        },
        indent=2,
        sort_keys=True,
    )
)
```

### Output

```json
{
  "eviction_policy": {
    "lru_casefold": "LRU",
    "score_normalized": "score"
  },
  "ranking_weights": {
    "default": {
      "sum": 1.0,
      "weights": {
        "bm25": 0.3,
        "semantic": 0.5,
        "source": 0.2
      }
    },
    "overweight_guard": "ConfigError raised",
    "partial_override": {
      "sum": 1.0,
      "weights": {
        "bm25": 0.2,
        "semantic": 0.6,
        "source": 0.19999999999999996
      }
    },
    "zero_rebalanced": {
      "sum": 1.0,
      "weights": {
        "bm25": 0.3333333333333333,
        "semantic": 0.3333333333333333,
        "source": 0.3333333333333333
      }
    }
  },
  "token_budget": {
    "invalid_-1": "ConfigError raised",
    "invalid_-16": "ConfigError raised",
    "invalid_0": "ConfigError raised",
    "numeric_string": 2048,
    "positive_int": 1024
  }
}
```

## Findings

- Default and partially overridden ranking weights normalise to a sum of `1.0`.
- Overweight inputs raise `ConfigError`, preventing silent renormalisation.
- Zero weights rebalance evenly so hybrid search remains deterministic.
- Token budgets accept positive integers (or numeric strings) and reject
  non-positive entries.
- Graph eviction policies normalise case, providing canonical identifiers to
  downstream consumers.
