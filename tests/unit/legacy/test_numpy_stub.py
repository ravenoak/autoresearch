import sys

import numpy as real_numpy

from typing import Any, cast

import tests.stubs.numpy as numpy_stub


def test_numpy_stub_manual_install(monkeypatch):
    """Real numpy remains untouched unless the stub is explicitly installed."""
    assert sys.modules["numpy"] is real_numpy

    # Manually swap in the stub
    monkeypatch.delitem(sys.modules, "numpy")
    monkeypatch.delitem(sys.modules, "numpy.random", raising=False)
    stub = cast(Any, numpy_stub).numpy_stub
    monkeypatch.setitem(sys.modules, "numpy", stub)
    monkeypatch.setitem(sys.modules, "numpy.random", stub.random)

    import numpy as np  # noqa: E402

    assert np is stub
    assert np.array(1) == []
    assert np.random.rand(1) == []
