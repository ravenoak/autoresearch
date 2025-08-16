"""Minimal stub for the :mod:`rdflib` package."""

import sys
import types

if "rdflib" not in sys.modules:
    rdflib_stub = types.ModuleType("rdflib")

    class Graph:
        pass

    rdflib_stub.Graph = Graph
    sys.modules["rdflib"] = rdflib_stub
