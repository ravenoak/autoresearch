"""Stub for the DuckDB VSS extension."""

import importlib.util
import sys
from types import ModuleType


if (
    importlib.util.find_spec("duckdb_extension_vss") is None
    and "duckdb_extension_vss" not in sys.modules
):
    module = ModuleType("duckdb_extension_vss")
    module.__version__ = "0.0"
    module.__spec__ = importlib.util.spec_from_loader(
        "duckdb_extension_vss", loader=None
    )
    sys.modules["duckdb_extension_vss"] = module
