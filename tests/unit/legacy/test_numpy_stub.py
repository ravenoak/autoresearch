# mypy: ignore-errors
import sys

import numpy as real_numpy

from typing import Any, cast

import tests.stubs.numpy as numpy_stub


def test_numpy_stub_manual_install(monkeypatch):
    """Real numpy remains untouched unless the stub is explicitly installed."""
    assert sys.modules["numpy"] is real_numpy

    # Test stub functionality directly without module replacement
    stub = cast(Any, numpy_stub).numpy_stub

    # Test that stub methods work as expected
    assert stub.array(1) == []
    # Test the rand function directly from the stub module
    from tests.stubs.numpy import rand
    result = rand(1)
    assert isinstance(result, list) and result == []
