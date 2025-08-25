"""Load behavior fixtures when running feature files directly."""

import sys
from pathlib import Path

# Ensure repository root on sys.path for imports
ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Import behavior-level fixtures and plugin registrations
from tests.behavior.conftest import *  # noqa: F401,F403,E402
