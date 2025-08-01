"""Stub for :mod:`transformers` to prevent model downloads."""

import sys
from unittest.mock import MagicMock

sys.modules.setdefault("transformers", MagicMock())
