"""Minimal stub for the :mod:`networkx` package."""

import sys
import types

if "networkx" not in sys.modules:
    nx_stub = types.ModuleType("networkx")

    class Graph:
        pass

    nx_stub.Graph = Graph
    sys.modules["networkx"] = nx_stub
