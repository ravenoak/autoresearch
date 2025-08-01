"""Stub for :mod:`matplotlib` and :mod:`matplotlib.pyplot`."""

import importlib.machinery
import sys
import types

if "matplotlib" not in sys.modules:
    mpl = types.ModuleType("matplotlib")
    mpl.use = lambda *a, **k: None
    mpl.__spec__ = importlib.machinery.ModuleSpec("matplotlib", loader=None)
    sys.modules["matplotlib"] = mpl

if "matplotlib.pyplot" not in sys.modules:
    mpl_py = types.ModuleType("matplotlib.pyplot")
    mpl_py.plot = lambda *a, **k: None
    mpl_py.figure = lambda *a, **k: None
    mpl_py.gca = lambda *a, **k: types.SimpleNamespace()
    mpl_py.savefig = lambda *a, **k: None
    mpl_py.__spec__ = importlib.machinery.ModuleSpec("matplotlib.pyplot", loader=None)
    sys.modules["matplotlib.pyplot"] = mpl_py
