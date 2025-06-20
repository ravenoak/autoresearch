#!/usr/bin/env python
"""Visualize the RDF knowledge graph as a PNG image."""

from pathlib import Path
import argparse

from autoresearch.storage import StorageManager


def main():
    parser = argparse.ArgumentParser(description="Visualize RDF store")
    parser.add_argument("output", nargs="?", default="rdf_graph.png", help="Output PNG path")
    args = parser.parse_args()

    StorageManager.setup()
    StorageManager.visualize_rdf(args.output)
    print(f"Graph written to {args.output}")


if __name__ == "__main__":
    main()
