import json
from pathlib import Path

import pytest

pytestmark = pytest.mark.slow

BASELINE_FILE = Path(__file__).resolve().parents[1] / "data" / "token_baselines.json"


@pytest.fixture
def token_baseline(request):
    """Record and compare token usage across test runs."""

    def _check(tokens, tolerance: int = 0) -> None:
        data = json.loads(BASELINE_FILE.read_text()) if BASELINE_FILE.exists() else {}
        test_id = request.node.nodeid
        baseline = data.get(test_id)
        if baseline is not None:
            for agent, counts in tokens.items():
                base_counts = baseline.get(agent, {})
                for direction in ("in", "out"):
                    measured = counts.get(direction, 0)
                    expected = base_counts.get(direction, 0)
                    delta = abs(measured - expected)
                    assert delta <= tolerance, (
                        f"{test_id} {agent} {direction} delta {delta} exceeds tolerance {tolerance}"
                    )
        data[test_id] = tokens
        BASELINE_FILE.write_text(json.dumps(data, indent=2, sort_keys=True))

    return _check
