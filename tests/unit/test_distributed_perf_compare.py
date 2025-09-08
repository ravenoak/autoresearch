from importlib.machinery import SourceFileLoader
from pathlib import Path


def _load_module():
    path = Path(__file__).resolve().parents[2] / "scripts" / "distributed_perf_compare.py"
    return SourceFileLoader("distributed_perf_compare", str(path)).load_module()


def test_compare_matches_theory_within_tolerance():
    mod = _load_module()
    results = mod.compare(
        max_workers=2,
        arrival_rate=80,
        service_rate=100,
        tasks=200,
        network_delay=0.0,
        seed=42,
    )
    for entry in results:
        pred = entry["predicted"]
        meas = entry["measured"]
        assert abs(pred["throughput"] - meas["throughput"]) / pred["throughput"] < 0.3
        assert abs(pred["latency_s"] - meas["latency_s"]) / pred["latency_s"] < 0.3
