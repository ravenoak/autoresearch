"""Stub for :mod:`torch` used in the test suite."""

import sys
from unittest.mock import MagicMock

if "torch" not in sys.modules:
    sys.modules["torch"] = MagicMock()
