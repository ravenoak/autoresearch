"""Wrapper script for exercising the Streamlit app in tests."""

from __future__ import annotations

import runpy
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

runpy.run_module("autoresearch.streamlit_app", run_name="__main__")
