# mypy: ignore-errors
"""Wrapper script for exercising the Streamlit app in tests."""

from __future__ import annotations

import os
import runpy
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Set test mode environment variable for the streamlit app
os.environ["_STREAMLIT_TEST_MODE"] = "true"

runpy.run_module("autoresearch.streamlit_app", run_name="__main__")
