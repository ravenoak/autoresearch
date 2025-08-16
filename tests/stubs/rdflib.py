"""Minimal stub for the :mod:`rdflib` package."""

import sys
import types

if "rdflib" not in sys.modules:
    rdflib_stub = types.ModuleType("rdflib")

    class Graph:
        def __init__(self, *args, **kwargs):
            """Minimal RDF graph stub accepting any arguments."""
            pass

        def open(self, *args, **kwargs):
            """Stub open method returning self."""
            return self

    rdflib_stub.Graph = Graph
    sys.modules["rdflib"] = rdflib_stub
