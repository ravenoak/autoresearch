"""Minimal stub for the :mod:`limits` package."""

import sys
import types

if "limits" not in sys.modules:
    limits_stub = types.ModuleType("limits")
    util_mod = types.ModuleType("limits.util")
    util_mod.parse = lambda s: s
    sys.modules["limits"] = limits_stub
    sys.modules["limits.util"] = util_mod
