from autoresearch.storage import StorageManager
from autoresearch.search import Search


def test_query_latency_and_memory(benchmark):
    query = "performance benchmark"

    def run():
        Search.generate_queries(query)

    memory_before = StorageManager._current_ram_mb()
    benchmark(run)
    memory_after = StorageManager._current_ram_mb()
    assert memory_after - memory_before < 10
