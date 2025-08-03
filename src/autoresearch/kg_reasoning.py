"""Helper utilities for ontology reasoning and advanced SPARQL queries."""

from __future__ import annotations

from importlib import import_module
from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional

import warnings
import rdflib

try:  # pragma: no cover - optional dependency
    import owlrl  # type: ignore
except Exception:  # pragma: no cover - fallback for offline tests
    class _DeductiveClosure:
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            """No-op constructor for fallback reasoner."""

        def expand(self, graph: rdflib.Graph) -> None:
            """No-op expansion when owlrl is unavailable."""

    @dataclass(frozen=True)
    class OwlRLStub:
        OWLRL_Semantics: object
        RDFS_Semantics: object
        DeductiveClosure: type

    owlrl = OwlRLStub(  # type: ignore
        OWLRL_Semantics=object(),
        RDFS_Semantics=object(),
        DeductiveClosure=_DeductiveClosure,
    )
    warnings.warn(
        "owlrl not installed; ontology reasoning will be skipped",
        RuntimeWarning,
    )

from .config import ConfigLoader
from .errors import StorageError


# Registry for pluggable ontology reasoners
_REASONER_PLUGINS: Dict[str, Callable[[rdflib.Graph], None]] = {}


def register_reasoner(name: str) -> Callable[[Callable[[rdflib.Graph], None]], Callable[[rdflib.Graph], None]]:
    """Register a reasoning plugin under ``name``.

    The returned decorator registers ``func`` as the handler for the given
    reasoner name, allowing ``run_ontology_reasoner`` to invoke it when
    configured.
    """

    def decorator(func: Callable[[rdflib.Graph], None]) -> Callable[[rdflib.Graph], None]:
        _REASONER_PLUGINS[name] = func
        return func

    return decorator


@register_reasoner("owlrl")
def _owlrl_reasoner(store: rdflib.Graph) -> None:
    """Apply OWL RL reasoning using ``owlrl`` if available."""

    try:  # pragma: no cover - optional dependency
        owlrl.DeductiveClosure(owlrl.OWLRL_Semantics).expand(store)
    except Exception as exc:  # pragma: no cover - optional dependency
        raise StorageError(
            "Failed to apply owlrl reasoning",
            cause=exc,
            suggestion="Ensure the owlrl package is installed",
        )


@register_reasoner("rdfs")
def _rdfs_reasoner(store: rdflib.Graph) -> None:
    """Apply RDFS reasoning using ``owlrl`` if available."""

    try:  # pragma: no cover - optional dependency
        owlrl.DeductiveClosure(owlrl.RDFS_Semantics).expand(store)
    except Exception as exc:  # pragma: no cover - optional dependency
        raise StorageError(
            "Failed to apply RDFS reasoning",
            cause=exc,
            suggestion="Ensure the owlrl package is installed",
        )


def run_ontology_reasoner(store: rdflib.Graph, engine: Optional[str] = None) -> None:
    """Apply ontology reasoning over ``store`` using the configured engine."""

    reasoner_setting = engine or getattr(
        ConfigLoader().config.storage, "ontology_reasoner", "owlrl"
    )
    reasoner = str(reasoner_setting)

    if reasoner in _REASONER_PLUGINS:
        try:
            _REASONER_PLUGINS[reasoner](store)
        except StorageError:
            raise
        except Exception as exc:
            raise StorageError(
                f"Failed to apply {reasoner} reasoning",
                cause=exc,
                suggestion="Ensure the ontology reasoner plugin is correctly installed",
            )
    elif ":" in reasoner:  # pragma: no cover - external reasoners optional
        try:
            module, func = reasoner.split(":", maxsplit=1)
            mod = import_module(module)
            getattr(mod, func)(store)
        except Exception as exc:
            raise StorageError(
                "Failed to run external ontology reasoner",
                cause=exc,
                suggestion="Check storage.ontology_reasoner configuration",
            )
    else:
        raise StorageError(
            f"Unknown ontology reasoner: {reasoner}",
            suggestion="Register the reasoner via register_reasoner or use 'module:function'",
        )


def query_with_reasoning(store: rdflib.Graph, query: str, engine: Optional[str] = None):
    """Run a SPARQL query after applying ontology reasoning."""

    run_ontology_reasoner(store, engine)
    return store.query(query)


__all__ = [
    "run_ontology_reasoner",
    "query_with_reasoning",
    "register_reasoner",
]
