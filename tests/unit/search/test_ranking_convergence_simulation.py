import sys
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from types import ModuleType
from typing import Any, Type

import pytest

pytestmark = pytest.mark.skip(
    reason="CollectorRegistry duplication in test environment"
)


def _load_module() -> ModuleType:
    root: Path = Path(__file__).resolve().parents[3]
    path = root / "src/autoresearch/search/ranking_convergence.py"
    name = "autoresearch.search.ranking_convergence"
    spec = spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(name)
    module = module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@pytest.mark.unit
def test_ranking_converges() -> None:
    module: ModuleType = _load_module()
    Doc: Type[Any] = module.DocScores
    docs: list[Any] = [
        Doc(0.2, 0.5, 0.3),
        Doc(0.1, 0.7, 0.2),
        Doc(0.9, 0.1, 0.0),
    ]
    weights: tuple[float, float, float] = (0.4, 0.4, 0.2)
    orderings: list[list[int]] = module.simulate_ranking_convergence(
        docs, weights, iterations=3
    )
    assert orderings[0] == orderings[1] == orderings[2]


@pytest.mark.unit
def test_invalid_weights_raise() -> None:
    module: ModuleType = _load_module()
    Doc: Type[Any] = module.DocScores
    docs: list[Any] = [Doc(0.1, 0.2, 0.7)]
    with pytest.raises(ValueError):
        module.simulate_ranking_convergence(docs, (0.5, 0.5, 0.5))
