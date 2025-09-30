import sys
from types import ModuleType
from unittest.mock import MagicMock

import pytest

from autoresearch.models import QueryResponse
from autoresearch.visualization import save_knowledge_graph
from pathlib import Path
from typing import Any


class DummyGraph:
    def add_node(self, *args, **kwargs):
        pass

    def add_edge(self, *args, **kwargs):
        pass


@pytest.fixture(autouse=True)
def fake_deps(monkeypatch):
    """Provide dummy matplotlib and networkx implementations."""
    fake_plt = ModuleType("pyplot")
    setattr(fake_plt, "figure", lambda *a, **k: None)
    setattr(fake_plt, "tight_layout", lambda *a, **k: None)
    setattr(fake_plt, "close", lambda *a, **k: None)
    setattr(fake_plt, "savefig", MagicMock())
    setattr(fake_plt, "gcf", lambda: None)
    monkeypatch.setitem(sys.modules, "matplotlib.pyplot", fake_plt)
    monkeypatch.setattr("autoresearch.visualization.plt", fake_plt, raising=False)

    fake_mpl = ModuleType("matplotlib")
    setattr(fake_mpl, "use", lambda *a, **k: None)
    monkeypatch.setitem(sys.modules, "matplotlib", fake_mpl)

    import networkx as real_nx

    monkeypatch.setattr(real_nx, "DiGraph", lambda *a, **k: DummyGraph())
    monkeypatch.setattr(real_nx, "draw", lambda *a, **k: None)
    monkeypatch.setattr(real_nx, "spring_layout", lambda *a, **k: {})
    monkeypatch.setattr(real_nx, "circular_layout", lambda *a, **k: {})
    monkeypatch.setattr("autoresearch.visualization.nx", real_nx, raising=False)

    yield fake_plt


def test_save_knowledge_graph(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, fake_deps: Any) -> None:
    plt = fake_deps
    response = QueryResponse(
        answer="a",
        citations=["c1", "c2"],
        reasoning=["r1", "r2"],
        metrics={},
    )
    out_file = tmp_path / "graph.png"
    save_knowledge_graph(response, str(out_file))
    plt.savefig.assert_called_once_with(str(out_file))


def test_save_knowledge_graph_spring_fallback(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, fake_deps: Any) -> None:
    plt = fake_deps
    response = QueryResponse(answer="a", citations=[], reasoning=["r"], metrics={})
    out_file = tmp_path / "graph.png"
    import networkx as real_nx

    def boom(*args, **kwargs):
        raise ValueError("fail")

    monkeypatch.setattr(real_nx, "spring_layout", boom)
    fallback = MagicMock(return_value={})
    monkeypatch.setattr(real_nx, "circular_layout", fallback)
    monkeypatch.setattr("autoresearch.visualization.nx", real_nx, raising=False)

    save_knowledge_graph(response, str(out_file), layout="spring")
    assert fallback.called
    plt.savefig.assert_called_with(str(out_file))
