"""Stub for :mod:`spacy` to avoid heavy import during tests."""

import sys
from unittest.mock import MagicMock

if "spacy" not in sys.modules:
    sys.modules["spacy"] = MagicMock()
