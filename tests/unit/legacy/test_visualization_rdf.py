# mypy: ignore-errors
"""Tests for RDF graph visualization helper."""

from __future__ import annotations

from pathlib import Path

import rdflib

from autoresearch.visualization import save_rdf_graph


def test_save_rdf_graph(tmp_path: Path) -> None:
    graph = rdflib.Graph()
    graph.add((rdflib.URIRef("s"), rdflib.URIRef("p"), rdflib.URIRef("o")))
    out = tmp_path / "g.png"
    save_rdf_graph(graph, str(out))
    data = out.read_bytes()
    assert data.startswith(b"\x89PNG")
