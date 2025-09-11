"""Stub for the :mod:`PIL` package."""

import importlib.util
import sys
import types

if importlib.util.find_spec("PIL") is None and "PIL" not in sys.modules:
    pil_mod = types.ModuleType("PIL")
    image_mod = types.ModuleType("PIL.Image")
    image_mod.Image = object
    pil_mod.Image = image_mod
    sys.modules["PIL"] = pil_mod
    sys.modules["PIL.Image"] = image_mod
