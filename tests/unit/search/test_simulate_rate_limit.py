import sys
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

import pytest

def _load_module():
    root = Path(__file__).resolve().parents[3]
    path = root / "src/autoresearch/search/simulate_rate_limit.py"
    name = "autoresearch.search.simulate_rate_limit"
    spec = spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(name)
    module = module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@pytest.mark.unit
def test_default_backoff():
    mod = _load_module()
    assert mod.simulate_rate_limit() == [0.2, 0.4, 0.8]


@pytest.mark.unit
def test_custom_backoff():
    mod = _load_module()
    assert mod.simulate_rate_limit(backoff_factor=1.0, max_retries=4) == [1.0, 2.0, 4.0, 8.0]
