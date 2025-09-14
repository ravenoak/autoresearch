#!/usr/bin/env python3
"""Simulate idempotent OxiGraph setup and teardown.

Usage:
    uv run python scripts/oxigraph_backend_sim.py --path /tmp/rdf_store
"""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path

import rdflib
from oxrdflib import OxigraphStore


def setup_store(path: Path) -> None:
    """Create the store at ``path`` if needed and close it immediately."""
    store = OxigraphStore()
    graph = rdflib.Graph(store=store)
    cfg = str(path)
    if path.exists():
        graph.open(configuration=cfg)
    else:
        graph.open(configuration=cfg, create=True)
    graph.close()


def teardown_store(path: Path) -> None:
    """Remove the store directory if it exists."""
    shutil.rmtree(path, ignore_errors=True)


def main(path: Path) -> None:
    setup_store(path)
    setup_store(path)
    teardown_store(path)
    teardown_store(path)
    print("completed")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--path",
        type=Path,
        default=Path("rdf_store"),
        help="Directory for the OxiGraph store",
    )
    args = parser.parse_args()
    main(args.path)
