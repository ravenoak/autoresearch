"""Tests for the ResultAggregator process."""

import multiprocessing

from autoresearch.distributed.coordinator import ResultAggregator


def test_result_aggregator_collects_messages() -> None:
    """Aggregator records results in publish order."""

    queue: multiprocessing.Queue[dict[str, int]] = multiprocessing.Queue()
    aggregator = ResultAggregator(queue)
    aggregator.start()
    queue.put({"action": "agent_result", "id": 1})
    queue.put({"action": "agent_result", "id": 2})
    queue.put({"action": "stop"})
    aggregator.join()

    assert [m["id"] for m in aggregator.results] == [1, 2]
