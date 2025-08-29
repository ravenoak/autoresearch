import sys
import pytest
from importlib.machinery import SourceFileLoader
from importlib.util import module_from_spec, spec_from_loader
from pathlib import Path


def _load_module():
    root = Path(__file__).resolve().parents[3]
    path = root / "src/autoresearch/search/ranking_convergence.py"
    name = "src.autoresearch.search.ranking_convergence"
    loader = SourceFileLoader(name, str(path))
    spec = spec_from_loader(name, loader)
    module = module_from_spec(spec)
    module.__package__ = "src.autoresearch.search"
    sys.modules[name] = module
    loader.exec_module(module)
    return module


@pytest.mark.unit
def test_ranking_converges():
    module = _load_module()
    Doc = module.DocScores
    docs = [
        Doc(0.2, 0.5, 0.3),
        Doc(0.1, 0.7, 0.2),
        Doc(0.9, 0.1, 0.0),
    ]
    weights = (0.4, 0.4, 0.2)
    orderings = module.simulate_ranking_convergence(docs, weights, iterations=3)
    assert orderings[0] == orderings[1] == orderings[2]


@pytest.mark.unit
def test_invalid_weights_raise():
    module = _load_module()
    Doc = module.DocScores
    docs = [Doc(0.1, 0.2, 0.7)]
    with pytest.raises(ValueError):
        module.simulate_ranking_convergence(docs, (0.5, 0.5, 0.5))
