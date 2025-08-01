"""Stub for :mod:`bertopic` to avoid heavy model downloads."""

import sys
from unittest.mock import MagicMock

sys.modules.setdefault("bertopic", MagicMock())
