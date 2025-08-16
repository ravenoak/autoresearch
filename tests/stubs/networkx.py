"""Minimal stub for the :mod:`networkx` package."""

import sys
import types

if "networkx" not in sys.modules:
    nx_stub = types.ModuleType("networkx")

    class Graph:
        def __init__(self, *args, **kwargs):
            """Minimal graph stub accepting any arguments."""
            pass

    class DiGraph(Graph):
        """Minimal directed graph stub."""

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)

    nx_stub.Graph = Graph
    nx_stub.DiGraph = DiGraph
    sys.modules["networkx"] = nx_stub
