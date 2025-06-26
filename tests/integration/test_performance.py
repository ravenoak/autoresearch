import json
from pathlib import Path

from autoresearch.storage import StorageManager
from autoresearch.search import Search
import importlib.util

SCRIPT_PATH = Path(__file__).resolve().parents[2] / "scripts" / "benchmark_token_memory.py"
spec = importlib.util.spec_from_file_location("benchmark_token_memory", SCRIPT_PATH)
benchmark_module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(benchmark_module)  # type: ignore
run_benchmark = benchmark_module.run_benchmark

BASELINE_PATH = Path(__file__).resolve().parent / "baselines" / "token_memory.json"


def test_query_latency_and_memory(benchmark):
    query = "performance benchmark"

    def run():
        Search.generate_queries(query)

    memory_before = StorageManager._current_ram_mb()
    benchmark(run)
    memory_after = StorageManager._current_ram_mb()
    assert memory_after - memory_before < 10

    metrics = run_benchmark()
    baseline = json.loads(BASELINE_PATH.read_text())
    assert metrics["tokens"] == baseline["tokens"]
    assert metrics["memory_delta_mb"] <= baseline["memory_delta_mb"] + 5
