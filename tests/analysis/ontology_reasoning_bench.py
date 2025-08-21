"""Benchmark ontology reasoning time versus triple count."""

from __future__ import annotations

import json
import time
from pathlib import Path

import rdflib

from autoresearch.kg_reasoning import run_ontology_reasoner


def _gen_graph(n: int) -> rdflib.Graph:
    g = rdflib.Graph()
    for i in range(n):
        s = rdflib.URIRef(f"urn:s{i}")
        p = rdflib.URIRef("urn:p")
        o = rdflib.URIRef(f"urn:o{i}")
        g.add((s, p, o))
    return g


def simulate(counts: list[int] | None = None) -> dict[str, list[dict[str, float]]]:
    """Measure reasoning time for increasing triple counts."""
    if counts is None:
        counts = [10, 50, 100, 200]
    results: list[dict[str, float]] = []
    for n in counts:
        g = _gen_graph(n)
        start = time.perf_counter()
        run_ontology_reasoner(g)
        elapsed = time.perf_counter() - start
        results.append({"triples": n, "seconds": elapsed})
    out_path = Path(__file__).with_name("ontology_reasoning_metrics.json")
    out_path.write_text(json.dumps(results, indent=2) + "\n")
    return {"results": results}


def run() -> dict[str, list[dict[str, float]]]:
    """Entry point for running the benchmark."""
    return simulate()


if __name__ == "__main__":  # pragma: no cover
    print(json.dumps(run(), indent=2))
