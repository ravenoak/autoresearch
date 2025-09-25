"""Configuration helpers tailored for unit tests.

These dataclasses provide a light-weight stand-in for :class:`ConfigModel`
instances. They expose the attributes accessed by orchestrator and search
unit tests without importing the full pydantic models.  Factory helpers
produce instances with sensible defaults while still allowing tests to
override specific fields explicitly.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field, replace
from typing import Any, Dict, Mapping, Optional


@dataclass(slots=True)
class ContextAwareSearchConfigStub:
    """Subset of context-aware search settings required in unit tests."""

    enabled: bool = True
    use_query_expansion: bool = True
    expansion_factor: float = 0.3
    use_search_history: bool = True
    max_history_items: int = 10


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

    def model_dump(self) -> Dict[str, Any]:
        """Return a dictionary representation mirroring ``BaseModel``."""

        return asdict(self)


def make_context_aware_config(
    overrides: Mapping[str, Any] | None = None,
) -> ContextAwareSearchConfigStub:
    """Return a context-aware configuration stub with optional overrides."""

    if overrides is None:
        return ContextAwareSearchConfigStub()
    return replace(ContextAwareSearchConfigStub(), **overrides)


def make_search_config(
    *,
    context_overrides: Mapping[str, Any] | None = None,
    overrides: Mapping[str, Any] | None = None,
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
    search_overrides: Mapping[str, Any] | None = None,
    context_overrides: Mapping[str, Any] | None = None,
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
