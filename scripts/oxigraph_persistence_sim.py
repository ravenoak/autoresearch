#!/usr/bin/env python3
"""Simulate OxiGraph setup cycles and optional teardown.

Usage:
    uv run python scripts/oxigraph_persistence_sim.py --runs 3 --force
"""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path

import rdflib
from oxrdflib import OxigraphStore


SENTINEL = (
    rdflib.URIRef("urn:test"),
    rdflib.URIRef("urn:p"),
    rdflib.Literal("v"),
)
# Fixed triple used to detect whether state survives between runs.


def init_store(path: Path) -> rdflib.Graph:
    """Open the store at ``path`` creating it if needed."""

    store = OxigraphStore()
    graph = rdflib.Graph(store=store)
    cfg = str(path)
    if path.exists():
        # Reuse existing store without the create flag.
        graph.open(configuration=cfg)
    else:
        # First initialization writes schema and data to disk.
        graph.open(configuration=cfg, create=True)
    return graph


def cycle(path: Path, runs: int) -> None:
    """Run ``runs`` setup cycles verifying persistence."""

    if runs <= 0:
        raise SystemExit("runs must be positive")
    for i in range(runs):
        graph = init_store(path)
        if i == 0:
            # Insert the sentinel once; later cycles verify persistence.
            graph.add(SENTINEL)
        else:
            # Reopening the store should retain the sentinel triple.
            assert SENTINEL in graph
        graph.close()


def teardown(path: Path, force: bool) -> None:
    """Remove ``path`` when ``force`` is true."""

    if path.exists():
        if not force:
            raise SystemExit("refusing to remove existing path; use --force")
        shutil.rmtree(path)


def main(path: Path, runs: int, force: bool) -> None:
    cycle(path, runs)
    teardown(path, force)
    print(f"completed {runs} cycles")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--path", type=Path, default=Path("rdf_store"))
    parser.add_argument("--runs", type=int, default=2)
    parser.add_argument(
        "--force",
        action="store_true",
        help="remove store path after simulation",
    )
    args = parser.parse_args()
    main(args.path, args.runs, args.force)
