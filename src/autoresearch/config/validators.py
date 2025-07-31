from __future__ import annotations

from typing import TYPE_CHECKING

from ..errors import ConfigError
from ..orchestration import ReasoningMode

if TYPE_CHECKING:
    from .models import SearchConfig


def validate_rdf_backend(cls, v: str) -> str:
    """Validate the RDF backend configuration."""
    valid_backends = ["sqlite", "berkeleydb", "memory"]
    if v not in valid_backends:
        raise ConfigError(
            "Invalid RDF backend", valid_backends=valid_backends, provided=v
        )
    return v


def normalize_ranking_weights(self: "SearchConfig") -> "SearchConfig":
    """Ensure relevance weights sum to ``1.0``."""
    default_weights = {
        "semantic_similarity_weight": 0.5,
        "bm25_weight": 0.3,
        "source_credibility_weight": 0.2,
    }
    weight_fields = set(default_weights.keys())
    provided = self.model_fields_set & weight_fields
    weights = {name: getattr(self, name) for name in weight_fields}

    if provided != weight_fields:
        remaining = 1.0 - sum(weights[n] for n in provided)
        if remaining < -0.001:
            raise ConfigError(
                "Relevance ranking weights must sum to 1.0",
                current_sum=sum(weights[n] for n in provided),
                weights={n: weights[n] for n in provided},
                suggestion="Decrease the provided weights so they do not exceed 1.0",
            )
        missing = weight_fields - provided
        defaults_total = sum(default_weights[n] for n in missing)
        for name in missing:
            setattr(
                self,
                name,
                remaining * default_weights[name] / defaults_total if defaults_total else 0.0,
            )
        weights = {n: getattr(self, n) for n in weight_fields}

    total = sum(weights.values())
    if abs(total - 1.0) > 0.001:
        raise ConfigError(
            "Relevance ranking weights must sum to 1.0",
            current_sum=total,
            weights=weights,
            suggestion="Adjust the weights so they sum to 1.0",
        )
    return self


def validate_reasoning_mode(cls, v: ReasoningMode | str) -> ReasoningMode:
    """Validate and convert the reasoning mode configuration."""
    if isinstance(v, ReasoningMode):
        return v
    try:
        return ReasoningMode(v)
    except Exception as exc:
        valid_modes = [m.value for m in ReasoningMode]
        raise ConfigError(
            "Invalid reasoning mode",
            valid_modes=valid_modes,
            provided=v,
            suggestion=f"Try using one of the valid modes: {', '.join(valid_modes)}",
            cause=exc,
        ) from exc


def validate_token_budget(cls, v: int | None) -> int | None:
    """Ensure the token budget is positive when provided."""
    if v is not None and v <= 0:
        raise ConfigError(
            "token_budget must be positive",
            provided=v,
            suggestion="Set token_budget to a positive integer or omit it",
        )
    return v


def validate_eviction_policy(cls, v: str) -> str:
    """Validate the graph eviction policy configuration."""
    valid_policies = ["LRU", "score"]
    if v not in valid_policies:
        raise ConfigError(
            "Invalid graph eviction policy",
            valid_policies=valid_policies,
            provided=v,
        )
    return v
