import types
import sys
from autoresearch.orchestration.orchestrator import Orchestrator
from autoresearch.models import QueryResponse


def test_get_memory_usage_psutil(monkeypatch):
    mock_proc = types.SimpleNamespace(memory_info=lambda: types.SimpleNamespace(rss=1024*1024))
    mock_psutil = types.SimpleNamespace(Process=lambda: mock_proc)
    monkeypatch.setitem(sys.modules, 'psutil', mock_psutil)
    assert Orchestrator._get_memory_usage() == 1.0


def test_calculate_result_confidence_bounds():
    resp = QueryResponse(answer='a', citations=['c']*3, reasoning=['r']*10,
                         metrics={'token_usage': {'total': 50, 'max_tokens': 100}, 'errors': []})
    score = Orchestrator._calculate_result_confidence(resp)
    assert 0.5 < score <= 1.0
