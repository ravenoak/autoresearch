import networkx as nx
from collections import OrderedDict
from hypothesis import given, strategies as st
from autoresearch import storage
from autoresearch.storage import StorageManager


@given(st.lists(st.text(min_size=1), unique=True, min_size=1, max_size=5))
def test_pop_lru_order(monkeypatch, ids):
    lru = OrderedDict((i, 0.0) for i in ids)
    monkeypatch.setattr(storage, "_lru", lru, raising=False)
    popped = [StorageManager._pop_lru() for _ in ids]
    assert popped == ids
    assert StorageManager._pop_lru() is None


@given(
    st.dictionaries(st.text(min_size=1), st.floats(min_value=0, max_value=1), min_size=1, max_size=5)
)
def test_pop_low_score(monkeypatch, node_conf):
    graph = nx.DiGraph()
    for node, score in node_conf.items():
        graph.add_node(node, confidence=float(score))
    lru = OrderedDict((node, 0.0) for node in node_conf)
    monkeypatch.setattr(storage.StorageManager.context, "graph", graph, raising=False)
    monkeypatch.setattr(storage, "_lru", lru, raising=False)

    expected = min(node_conf, key=node_conf.get)
    result = StorageManager._pop_low_score()
    assert result == expected
    assert result not in storage._lru


def test_current_ram_mb_non_negative():
    assert StorageManager._current_ram_mb() >= 0.0
