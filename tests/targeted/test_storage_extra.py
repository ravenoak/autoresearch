import networkx as nx
from autoresearch import storage


def test_pop_low_score(monkeypatch):
    g = nx.DiGraph()
    g.add_node('a', confidence=0.2)
    g.add_node('b', confidence=0.5)
    monkeypatch.setattr(storage, '_graph', g)
    monkeypatch.setattr(storage, '_lru', storage.OrderedDict())
    popped = storage.StorageManager._pop_low_score()
    assert popped == 'a'
