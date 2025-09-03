"""Stub for :mod:`bertopic` to avoid heavy model downloads."""

import importlib.util
import sys
from types import ModuleType

module = ModuleType("bertopic")
module.__version__ = "0.0"
module.__spec__ = importlib.util.spec_from_loader("bertopic", loader=None)
sys.modules.setdefault("bertopic", module)
