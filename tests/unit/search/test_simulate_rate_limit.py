import sys
import pytest
from importlib.machinery import SourceFileLoader
from importlib.util import module_from_spec, spec_from_loader
from pathlib import Path


def _load_module():
    root = Path(__file__).resolve().parents[3]
    path = root / "src/autoresearch/search/simulate_rate_limit.py"
    name = "src.autoresearch.search.simulate_rate_limit"
    loader = SourceFileLoader(name, str(path))
    spec = spec_from_loader(name, loader)
    module = module_from_spec(spec)
    module.__package__ = "src.autoresearch.search"
    sys.modules[name] = module
    loader.exec_module(module)
    return module


@pytest.mark.unit
def test_default_backoff():
    mod = _load_module()
    assert mod.simulate_rate_limit() == [0.2, 0.4, 0.8]


@pytest.mark.unit
def test_custom_backoff():
    mod = _load_module()
    assert mod.simulate_rate_limit(backoff_factor=1.0, max_retries=4) == [1.0, 2.0, 4.0, 8.0]
