from autoresearch.models import QueryResponse
from autoresearch.visualization import save_knowledge_graph

import importlib
import pytest

mpl = importlib.import_module("matplotlib")
if not getattr(mpl, "__file__", None):
    pytest.skip("real matplotlib not available", allow_module_level=True)


@pytest.mark.parametrize("layout", ["spring", "circular"])
def test_save_knowledge_graph(tmp_path, layout):
    response = QueryResponse(
        answer="a",
        citations=["c1"],
        reasoning=["r1"],
        metrics={},
    )
    out_file = tmp_path / "graph.png"
    save_knowledge_graph(response, str(out_file), layout=layout)
    assert out_file.exists() and out_file.stat().st_size > 0
