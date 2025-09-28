"""Helper utilities for ontology reasoning and advanced SPARQL queries."""

from __future__ import annotations

from importlib import import_module
from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional

import logging
import threading
import time
import warnings
import rdflib

try:  # pragma: no cover - optional dependency
    import owlrl
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
from .knowledge.graph import (  # noqa: F401
    GraphContradiction,
    GraphEntity,
    GraphExtractionSummary,
    GraphRelation,
    SessionGraphPipeline,
)


# Registry for pluggable ontology reasoners
_REASONER_PLUGINS: Dict[str, Callable[[rdflib.Graph], None]] = {}


def register_reasoner(
    name: str,
) -> Callable[[Callable[[rdflib.Graph], None]], Callable[[rdflib.Graph], None]]:
    """Register a reasoning plugin for use in the ontology pipeline.

    Args:
        name: Identifier under which the decorated callable is stored.

    Returns:
        A decorator that stores the wrapped callable in the global reasoner
        registry, keyed by ``name``.
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


def run_ontology_reasoner(
    store: rdflib.Graph, engine: Optional[str] = None
) -> None:
    """Apply ontology reasoning using the configured engine.

    Args:
        store: RDF graph that should be enriched with inferred triples.
        engine: Optional override for the reasoner name. When ``None`` the
            value from configuration is used.

    Raises:
        StorageError: If the configured reasoner is unknown, times out, or
            encounters an unrecoverable error during execution.
    """

    storage_cfg = ConfigLoader().config.storage
    reasoner_setting = engine or getattr(storage_cfg, "ontology_reasoner", "owlrl")
    reasoner = str(reasoner_setting)

    logger = logging.getLogger(__name__)
    triple_count = len(store)
    logger.info(
        "Starting ontology reasoning with %d triples using %s", triple_count, reasoner
    )

    max_triples = getattr(storage_cfg, "ontology_reasoner_max_triples", None)
    if max_triples is not None and triple_count > max_triples:
        logger.warning(
            "Skipping ontology reasoning for %d triples; limit is %d",
            triple_count,
            max_triples,
        )
        return

    start_time = time.perf_counter()

    def _apply_reasoner() -> None:
        if reasoner in _REASONER_PLUGINS:
            _REASONER_PLUGINS[reasoner](store)
        elif ":" in reasoner:  # pragma: no cover - external reasoners optional
            try:
                module, func = reasoner.split(":", maxsplit=1)
                mod = import_module(module)
                getattr(mod, func)(store)
            except Exception as exc:  # pragma: no cover - import failures optional
                raise StorageError(
                    "Failed to run external ontology reasoner",
                    cause=exc,
                    suggestion="Check storage.ontology_reasoner configuration",
                )
        else:
            raise StorageError(
                f"Unknown ontology reasoner: {reasoner}",
                suggestion=(
                    "Register the reasoner via register_reasoner or use 'module:function'"
                ),
            )

    error: list[BaseException] = []

    def _worker() -> None:
        try:
            _apply_reasoner()
        except BaseException as exc:  # capture all exceptions including KeyboardInterrupt
            error.append(exc)

    timeout = getattr(storage_cfg, "ontology_reasoner_timeout", None)

    if timeout is None:
        _worker()
    else:
        thread = threading.Thread(target=_worker, daemon=True)
        thread.start()
        thread.join(timeout)
        if thread.is_alive():
            raise StorageError(
                f"Ontology reasoner '{reasoner}' timed out after {timeout} seconds",
                suggestion=(
                    "Increase storage.ontology_reasoner_timeout or choose a lighter reasoner"
                ),
            )
        thread.join()

    if error:
        exc = error[0]
        if isinstance(exc, StorageError):
            raise exc
        if isinstance(exc, KeyboardInterrupt):
            raise StorageError(
                "Ontology reasoning interrupted",
                suggestion=(
                    "Adjust storage.ontology_reasoner_timeout or choose a lighter reasoner"
                ),
            ) from exc
        cause = exc if isinstance(exc, Exception) else None
        raise StorageError(
            f"Failed to apply {reasoner} reasoning",
            cause=cause,
            suggestion="Ensure the ontology reasoner plugin is correctly installed",
        ) from exc

    elapsed = time.perf_counter() - start_time
    logger.info(
        "Completed ontology reasoning with %d triples in %.2f seconds",
        len(store),
        elapsed,
    )


def query_with_reasoning(
    store: rdflib.Graph, query: str, engine: Optional[str] = None
):
    """Run a SPARQL query with ontology reasoning applied first.

    Args:
        store: RDF graph to query.
        query: SPARQL query string executed after reasoning.
        engine: Optional override for the reasoner name.

    Returns:
        The ``rdflib`` query result produced by evaluating ``query`` on the
        enriched ``store``.

    Raises:
        StorageError: If ontology reasoning fails before the query executes.
    """

    run_ontology_reasoner(store, engine)
    return store.query(query)


KnowledgeGraphPipeline = SessionGraphPipeline


__all__ = [
    'run_ontology_reasoner',
    'query_with_reasoning',
    'register_reasoner',
    'KnowledgeGraphPipeline',
    'SessionGraphPipeline',
    'GraphEntity',
    'GraphRelation',
    'GraphExtractionSummary',
    'GraphContradiction',
]
