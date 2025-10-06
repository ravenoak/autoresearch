# mypy: ignore-errors
"""Load behavior fixtures when running feature files directly."""

import sys
from pathlib import Path

# Import behavior-level fixtures and plugin registrations
import tests.behavior.conftest  # noqa: F401

# Ensure repository root on sys.path for imports
ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
