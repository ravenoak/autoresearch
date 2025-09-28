"""Configuration helpers tailored for unit tests.

These dataclasses provide a light-weight stand-in for :class:`ConfigModel`
instances. They expose the attributes accessed by orchestrator and search
unit tests without importing the full pydantic models. Factory helpers
produce instances with sensible defaults while still allowing tests to
override specific fields explicitly. TypedDict exports mirror the
structure produced by :meth:`ConfigModelStub.model_dump`.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Optional, TypedDict


class ContextAwareSearchConfigDump(TypedDict):
    """Serialized form of :class:`ContextAwareSearchConfigStub`."""

    enabled: bool
    use_query_expansion: bool
    expansion_factor: float
    use_search_history: bool
    max_history_items: int
    graph_signal_weight: float
    planner_graph_conditioning: bool


class SearchConfigDump(TypedDict):
    """Serialized representation of :class:`SearchConfigStub`."""

    context_aware: ContextAwareSearchConfigDump


class ConfigModelDump(TypedDict):
    """Structure returned by :meth:`ConfigModelStub.model_dump`."""

    token_budget: Optional[int]
    loops: int
    adaptive_max_factor: int
    adaptive_min_buffer: int
    search: SearchConfigDump
    gate_graph_contradiction_threshold: float
    gate_graph_similarity_threshold: float


ContextOverrideValue = bool | float | int


@dataclass(slots=True)
class ContextAwareSearchConfigStub:
    """Subset of context-aware search settings required in unit tests."""

    enabled: bool = True
    use_query_expansion: bool = True
    expansion_factor: float = 0.3
    use_search_history: bool = True
    max_history_items: int = 10
    graph_signal_weight: float = 0.2
    planner_graph_conditioning: bool = False


@dataclass(slots=True)
class SearchConfigStub:
    """Search configuration stub exposing the context-aware settings."""

    context_aware: ContextAwareSearchConfigStub = field(
        default_factory=ContextAwareSearchConfigStub
    )


@dataclass(slots=True)
class ConfigModelStub:
    """Minimal configuration object compatible with ``ConfigModel`` access."""

    token_budget: Optional[int] = None
    loops: int = 2
    adaptive_max_factor: int = 20
    adaptive_min_buffer: int = 10
    search: SearchConfigStub = field(default_factory=SearchConfigStub)
    gate_graph_contradiction_threshold: float = 0.25
    gate_graph_similarity_threshold: float = 0.0

    def model_dump(self) -> ConfigModelDump:
        """Return a dictionary representation mirroring ``BaseModel``."""

        return {
            "token_budget": self.token_budget,
            "loops": self.loops,
            "adaptive_max_factor": self.adaptive_max_factor,
            "adaptive_min_buffer": self.adaptive_min_buffer,
            "search": {
                "context_aware": {
                    "enabled": self.search.context_aware.enabled,
                    "use_query_expansion": (
                        self.search.context_aware.use_query_expansion
                    ),
                    "expansion_factor": self.search.context_aware.expansion_factor,
                    "use_search_history": (
                        self.search.context_aware.use_search_history
                    ),
                    "max_history_items": (
                        self.search.context_aware.max_history_items
                    ),
                    "graph_signal_weight": (
                        self.search.context_aware.graph_signal_weight
                    ),
                    "planner_graph_conditioning": (
                        self.search.context_aware.planner_graph_conditioning
                    ),
                },
            },
            "gate_graph_contradiction_threshold": (
                self.gate_graph_contradiction_threshold
            ),
            "gate_graph_similarity_threshold": self.gate_graph_similarity_threshold,
        }


def make_context_aware_config(
    overrides: Mapping[str, ContextOverrideValue] | None = None,
) -> ContextAwareSearchConfigStub:
    """Return a context-aware configuration stub with optional overrides."""

    config = ContextAwareSearchConfigStub()
    if not overrides:
        return config
    for key, value in overrides.items():
        if not hasattr(config, key):
            raise AttributeError(
                f"ContextAwareSearchConfigStub has no attribute '{key}'"
            )
        setattr(config, key, value)
    return config


SearchOverrideValue = bool | float | int


def make_search_config(
    *,
    context_overrides: Mapping[str, ContextOverrideValue] | None = None,
    overrides: Mapping[str, SearchOverrideValue] | None = None,
) -> SearchConfigStub:
    """Construct a search configuration stub for unit tests."""

    context_cfg = make_context_aware_config(context_overrides)
    search_cfg = SearchConfigStub(context_aware=context_cfg)
    if overrides:
        for key, value in overrides.items():
            if key == "context_aware":
                raise ValueError(
                    "Use 'context_overrides' to customise context-aware settings"
                )
            if not hasattr(search_cfg, key):
                raise AttributeError(
                    f"SearchConfigStub has no attribute '{key}' to override"
                )
            setattr(search_cfg, key, value)
    return search_cfg


def make_config_model(
    *,
    token_budget: Optional[int] = None,
    loops: int = 2,
    adaptive_max_factor: int = 20,
    adaptive_min_buffer: int = 10,
    search_overrides: Mapping[str, SearchOverrideValue] | None = None,
    context_overrides: Mapping[str, ContextOverrideValue] | None = None,
) -> ConfigModelStub:
    """Create a :class:`ConfigModelStub` with explicit overrides when needed."""

    search_cfg = make_search_config(
        context_overrides=context_overrides, overrides=search_overrides
    )
    return ConfigModelStub(
        token_budget=token_budget,
        loops=loops,
        adaptive_max_factor=adaptive_max_factor,
        adaptive_min_buffer=adaptive_min_buffer,
        search=search_cfg,
    )


__all__ = [
    "ConfigModelStub",
    "ContextAwareSearchConfigStub",
    "SearchConfigStub",
    "make_config_model",
    "make_search_config",
    "make_context_aware_config",
]
