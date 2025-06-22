"""Helper utilities for ontology reasoning and advanced SPARQL queries."""

from __future__ import annotations

from importlib import import_module
from typing import Optional

import rdflib

from .config import ConfigLoader
from .errors import StorageError


def run_ontology_reasoner(store: rdflib.Graph, engine: Optional[str] = None) -> None:
    """Apply ontology reasoning over ``store`` using the configured engine."""
    reasoner = engine or getattr(ConfigLoader().config.storage, "ontology_reasoner", "owlrl")
    if reasoner == "owlrl":
        try:  # pragma: no cover - optional dependency
            import owlrl  # type: ignore

            owlrl.DeductiveClosure(owlrl.OWLRL_Semantics).expand(store)
        except Exception as exc:  # pragma: no cover - optional dependency
            raise StorageError(
                "Failed to apply owlrl reasoning",
                cause=exc,
                suggestion="Ensure the owlrl package is installed",
            )
    else:  # pragma: no cover - external reasoners optional
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


def query_with_reasoning(store: rdflib.Graph, query: str, engine: Optional[str] = None):
    """Run a SPARQL query after applying ontology reasoning."""
    run_ontology_reasoner(store, engine)
    return store.query(query)
