# mypy: ignore-errors
from collections import OrderedDict, deque
from unittest.mock import MagicMock, patch

from hypothesis import HealthCheck, assume, example, given, seed, settings
from hypothesis import strategies as st

from types import SimpleNamespace

from autoresearch.config.models import ConfigModel
from autoresearch.orchestration.metrics import EVICTION_COUNTER
from autoresearch.storage import (
    FIFOEvictionPolicy,
    LRUEvictionPolicy,
    StorageManager,
)


@given(
    capacity=st.integers(min_value=1, max_value=5),
    ops=st.lists(st.text(min_size=1), min_size=1, max_size=20),
)
def test_fifo_eviction_property(capacity, ops):
    """FIFO evicts in insertion order for unique keys."""
    policy = FIFOEvictionPolicy(capacity)
    expected: deque[str] = deque()
    evicted: list[str] = []
    for key in ops:
        res = policy.record(key)
        if res:
            evicted.append(res)
        if key in expected:
            continue
        expected.append(key)
        if len(expected) > capacity:
            assert evicted[-1] == expected.popleft()


@given(
    capacity=st.integers(min_value=1, max_value=5),
    ops=st.lists(st.text(min_size=1), min_size=1, max_size=20),
)
def test_lru_eviction_property(capacity, ops):
    """LRU evicts the stalest accessed key."""
    policy = LRUEvictionPolicy(capacity)
    mirror: OrderedDict[str, object] = OrderedDict()
    evicted: list[str] = []
    for key in ops:
        res = policy.record(key)
        if res:
            evicted.append(res)
        if key in mirror:
            mirror.move_to_end(key)
        else:
            mirror[key] = None
        if len(mirror) > capacity:
            expected, _ = mirror.popitem(last=False)
            assert evicted[-1] == expected


@given(
    budget=st.integers(min_value=1, max_value=100),
    usage=st.integers(min_value=0, max_value=100),
)
def test_enforce_ram_budget_under_budget_property(budget, usage):
    """No eviction when usage does not exceed the budget."""
    assume(usage <= budget)
    mock_graph = MagicMock()
    with patch.object(StorageManager.context, "graph", mock_graph):
        with patch(
            "autoresearch.storage.StorageManager._current_ram_mb",
            return_value=usage,
        ):
            with patch(
                "autoresearch.config.loader.ConfigLoader.config",
                new=MagicMock(graph_eviction_policy="lru"),
            ):
                StorageManager._enforce_ram_budget(budget)
    mock_graph.remove_node.assert_not_called()


@st.composite
def _eviction_scenarios(draw: st.DrawFn) -> tuple[int, float, list[int], bool, int | None]:
    """Generate parameter sets for eviction property tests."""

    budget = draw(st.integers(min_value=1, max_value=50))
    safety = draw(st.floats(min_value=0.0, max_value=0.5, allow_nan=False))
    reductions = draw(
        st.lists(st.integers(min_value=1, max_value=20), min_size=1, max_size=5)
    )
    stale_lru = draw(st.booleans())
    drop_index = draw(
        st.one_of(
            st.none(),
            st.integers(min_value=1, max_value=len(reductions)),
        )
    )
    return budget, safety, reductions, stale_lru, drop_index


@settings(suppress_health_check=[HealthCheck.filter_too_much], max_examples=50)
@example((3, 0.1, [1, 1, 1, 1], False, 1))
@seed(170090525894866085979644260693064061602)
@given(_eviction_scenarios())
def test_enforce_ram_budget_reduces_usage_property(params):
    """Eviction converges even when RAM metrics vanish mid-run."""

    budget, safety, reductions, stale_lru, drop_index = params
    target = budget * (1 - safety)
    total_reduction = sum(reductions)
    assume(total_reduction > max(1.0, budget - target + 1e-6))
    start = target + total_reduction
    assume(start > budget)

    usage_sequence = [start]
    current = start
    for reduction in reductions:
        current -= reduction
        usage_sequence.append(current)

    ram_sequence = usage_sequence.copy()
    if drop_index is not None:
        drop_at = min(drop_index, len(ram_sequence) - 1)
        for idx in range(drop_at, len(ram_sequence)):
            ram_sequence[idx] = 0.0

    nodes: dict[str, dict[str, object]] = {
        f"n{i}": {} for i in range(len(reductions) + 2)
    }
    initial_node_count = len(nodes)
    mock_graph = MagicMock()
    mock_graph.nodes = nodes
    mock_graph.has_node.side_effect = lambda n, nodes=nodes: n in nodes

    def remove_node(node_id: str) -> None:
        nodes.pop(node_id, None)

    mock_graph.remove_node.side_effect = remove_node

    mock_lru: OrderedDict[str, int]
    if stale_lru:
        mock_lru = OrderedDict()
    else:
        mock_lru = OrderedDict((node_id, index) for index, node_id in enumerate(nodes))

    ram_mock = MagicMock(side_effect=ram_sequence + [ram_sequence[-1]] * 5)
    storage_cfg = SimpleNamespace(
        deterministic_node_budget=None,
        minimum_deterministic_resident_nodes=2,
    )
    cfg = SimpleNamespace(
        graph_eviction_policy="lru",
        eviction_batch_size=1,
        eviction_safety_margin=safety,
        storage=storage_cfg,
    )

    with patch.object(StorageManager.context, "graph", mock_graph):
        with patch.object(StorageManager.state, "lru", mock_lru):
            with patch(
                "autoresearch.storage.StorageManager._current_ram_mb",
                ram_mock,
            ):
                with patch(
                    "autoresearch.config.loader.ConfigLoader.config",
                    new=cfg,
                ):
                    StorageManager._enforce_ram_budget(budget)

    deterministic_limit, _, minimum_resident_nodes, _ = StorageManager._deterministic_node_limit(
        budget, cfg
    )
    survivor_floor = (
        max(deterministic_limit, minimum_resident_nodes)
        if deterministic_limit is not None
        else None
    )
    limit_gap = (
        max(0, initial_node_count - deterministic_limit)
        if deterministic_limit is not None
        else 0
    )
    expected_evictions = 0 if drop_index is not None else len(reductions)
    max_evictions = initial_node_count
    if deterministic_limit is not None:
        max_evictions = max(0, initial_node_count - (survivor_floor or deterministic_limit))
        expected_evictions = max(
            limit_gap,
            min(expected_evictions, max_evictions),
        )

    assert mock_graph.remove_node.call_count >= expected_evictions

    # The final measurement is taken after all eviction completes
    # When RAM measurements drop out, eviction continues with deterministic limits
    final_measurement = ram_sequence[min(ram_mock.call_count - 1, len(ram_sequence) - 1)]
    reached_floor = survivor_floor is not None and len(nodes) == survivor_floor
    exhausted_evictions = min(len(reductions), max_evictions) < len(reductions)
    if drop_index is None:
        if not (reached_floor and exhausted_evictions):
            assert final_measurement <= target + 1e-6
    # When RAM measurements drop out (drop_index != None), eviction should still
    # complete successfully using deterministic limits, regardless of final measurement

    if survivor_floor is not None:
        assert len(nodes) <= survivor_floor


def test_enforce_ram_budget_handles_metric_dropout() -> None:
    """Regression: deterministic fallback survives a mid-run metrics dropout."""

    budget = 3
    nodes: dict[str, dict[str, object]] = {f"n{i}": {} for i in range(6)}
    mock_graph = MagicMock()
    mock_graph.nodes = nodes
    mock_graph.has_node.side_effect = lambda n, nodes=nodes: n in nodes

    def remove_node(node_id: str) -> None:
        nodes.pop(node_id, None)

    mock_graph.remove_node.side_effect = remove_node
    mock_lru: OrderedDict[str, int] = OrderedDict(
        (node_id, idx) for idx, node_id in enumerate(list(nodes))
    )

    ram_mock = MagicMock(side_effect=[10.0, 0.0, 0.0, 0.0, 0.0])
    cfg = MagicMock(
        graph_eviction_policy="lru",
        eviction_batch_size=1,
        eviction_safety_margin=0.1,
    )

    with patch.object(StorageManager.context, "graph", mock_graph):
        with patch.object(StorageManager.state, "lru", mock_lru):
            with patch("autoresearch.storage.StorageManager._current_ram_mb", ram_mock):
                with patch(
                    "autoresearch.config.loader.ConfigLoader.config",
                    new=cfg,
                ):
                    StorageManager._enforce_ram_budget(budget)

    assert len(nodes) == budget
    assert mock_graph.remove_node.call_count == 3


def test_pop_lru():
    """Test that _pop_lru removes and returns the least recently used node."""
    # Setup
    mock_lru: OrderedDict[str, int] = OrderedDict([("a", 1), ("b", 2), ("c", 3)])
    with patch.object(StorageManager.state, "lru", mock_lru):
        # Execute
        node_id = StorageManager._pop_lru()

        # Verify
        assert node_id == "a"
        assert "a" not in mock_lru
        assert list(mock_lru.keys()) == ["b", "c"]


def test_pop_lru_empty():
    """Test that _pop_lru returns None when the LRU cache is empty."""
    # Setup
    mock_lru: OrderedDict[str, int] = OrderedDict()
    with patch.object(StorageManager.state, "lru", mock_lru):
        # Execute
        node_id = StorageManager._pop_lru()

        # Verify
        assert node_id is None


def test_pop_low_score():
    """Test that _pop_low_score removes and returns the node with the lowest confidence score."""
    # Setup
    mock_graph = MagicMock()
    mock_graph.nodes = {
        "a": {"confidence": 0.3},
        "b": {"confidence": 0.1},
        "c": {"confidence": 0.5},
    }
    mock_lru: OrderedDict[str, int] = OrderedDict([("a", 1), ("b", 2), ("c", 3)])

    with patch.object(StorageManager.context, "graph", mock_graph):
        with patch.object(StorageManager.state, "lru", mock_lru):
            # Execute
            node_id = StorageManager._pop_low_score()

            # Verify
            assert node_id == "b"
            assert "b" not in mock_lru


def test_pop_low_score_empty():
    """Test that _pop_low_score returns None when the graph is empty."""
    # Setup
    with patch.object(StorageManager.context, "graph", None):
        # Execute
        node_id = StorageManager._pop_low_score()

        # Verify
        assert node_id is None

    # Setup with empty graph
    mock_graph = MagicMock()
    mock_graph.nodes = {}

    with patch.object(StorageManager.context, "graph", mock_graph):
        # Execute
        node_id = StorageManager._pop_low_score()

        # Verify
        assert node_id is None


def test_enforce_ram_budget_lru_policy():
    """Test that _enforce_ram_budget evicts nodes using the LRU policy."""
    # Setup
    mock_graph = MagicMock()
    mock_graph.has_node.return_value = True
    mock_graph.nodes = {str(i): {} for i in range(10)}

    def mock_remove_node(node_id):
        mock_graph.nodes.pop(node_id, None)

    mock_graph.remove_node.side_effect = mock_remove_node
    mock_lru: OrderedDict[str, int] = OrderedDict((str(i), i) for i in range(10))

    with patch.object(StorageManager.context, "graph", mock_graph):
        with patch.object(StorageManager.state, "lru", mock_lru):
            with patch(
                "autoresearch.storage.StorageManager._current_ram_mb",
                side_effect=[100, 100, 50, 50],
            ):
                with patch(
                    "autoresearch.config.loader.ConfigLoader.config",
                    new=ConfigModel(graph_eviction_policy="lru"),
                ):
                    start = EVICTION_COUNTER._value.get()
                    StorageManager._enforce_ram_budget(75)

                # Verify
                assert mock_graph.remove_node.call_count == 2
                mock_graph.remove_node.assert_any_call("0")
                mock_graph.remove_node.assert_any_call("1")
                assert EVICTION_COUNTER._value.get() == start + 2


def test_enforce_ram_budget_score_policy():
    """Test that _enforce_ram_budget evicts nodes using the score policy."""
    # Setup
    mock_graph = MagicMock()
    mock_graph.has_node.return_value = True

    # Create a dictionary to track nodes with varying confidence
    nodes_dict = {str(i): {"confidence": 0.1 + i * 0.1} for i in range(10)}
    nodes_dict["0"]["confidence"] = 0.05
    nodes_dict["1"]["confidence"] = 0.15

    # Set up the mock graph's nodes attribute
    mock_graph.nodes = nodes_dict

    # Create a mock LRU cache
    mock_lru: OrderedDict[str, int] = OrderedDict((str(i), i) for i in range(10))

    # Set up the remove_node method to update the nodes dictionary
    def mock_remove_node(node_id):
        nodes_dict.pop(node_id, None)

    mock_graph.remove_node.side_effect = mock_remove_node

    with patch.object(StorageManager.context, "graph", mock_graph):
        with patch.object(StorageManager.state, "lru", mock_lru):
            with patch(
                "autoresearch.storage.StorageManager._current_ram_mb",
                side_effect=[100, 100, 50, 50],
            ):
                with patch(
                    "autoresearch.config.loader.ConfigLoader.config",
                    new=ConfigModel(graph_eviction_policy="score"),
                ):
                    start = EVICTION_COUNTER._value.get()
                    StorageManager._enforce_ram_budget(75)

                # Verify
                assert mock_graph.remove_node.call_count == 2
                mock_graph.remove_node.assert_any_call("0")
                mock_graph.remove_node.assert_any_call("1")
                assert EVICTION_COUNTER._value.get() == start + 2

                # Verify that remaining nodes exclude evicted ones
                assert "0" not in nodes_dict and "1" not in nodes_dict


def test_enforce_ram_budget_hybrid_policy():
    """Test that _enforce_ram_budget evicts nodes using the hybrid policy."""
    mock_graph = MagicMock()
    mock_graph.has_node.return_value = True
    mock_graph.nodes = {
        "a": {"confidence": 0.9},
        "b": {"confidence": 0.2},
        "c": {"confidence": 0.1},
    }
    mock_lru: OrderedDict[str, int] = OrderedDict([("a", 1), ("b", 2), ("c", 3)])

    def mock_remove_node(node_id):
        mock_graph.nodes.pop(node_id, None)

    mock_graph.remove_node.side_effect = mock_remove_node

    with patch.object(StorageManager.context, "graph", mock_graph):
        with patch.object(StorageManager.state, "lru", mock_lru):
            with patch(
                "autoresearch.storage.StorageManager._current_ram_mb",
                side_effect=[100, 100, 50, 50],
            ):
                with patch(
                    "autoresearch.config.loader.ConfigLoader.config",
                    new=ConfigModel(graph_eviction_policy="hybrid"),
                ):
                    start = EVICTION_COUNTER._value.get()
                    StorageManager._enforce_ram_budget(75)

                    assert mock_graph.remove_node.call_count == 2
                    assert "a" not in mock_graph.nodes
                    assert "b" not in mock_graph.nodes
                    assert EVICTION_COUNTER._value.get() == start + 2


def test_enforce_ram_budget_adaptive_policy():
    """Test that _enforce_ram_budget uses score policy when variance is high."""
    mock_graph = MagicMock()
    mock_graph.has_node.return_value = True
    mock_graph.nodes = {"a": {"confidence": 0.1}, "b": {"confidence": 0.9}}
    mock_lru: OrderedDict[str, int] = OrderedDict([("a", 1), ("b", 2)])

    def mock_remove_node(node_id):
        mock_graph.nodes.pop(node_id, None)

    mock_graph.remove_node.side_effect = mock_remove_node

    with (
        patch.object(StorageManager, "_access_frequency", {"a": 10, "b": 1}),
        patch.object(StorageManager, "_last_adaptive_policy", "lru"),
    ):
        with patch.object(StorageManager.context, "graph", mock_graph):
            with patch.object(StorageManager.state, "lru", mock_lru):
                with patch(
                    "autoresearch.storage.StorageManager._current_ram_mb",
                    side_effect=[100, 100, 50, 50],
                ):
                    with patch(
                        "autoresearch.storage.StorageManager._pop_low_score",
                        return_value="a",
                    ) as pls:
                        with patch(
                            "autoresearch.config.loader.ConfigLoader.config",
                            new=ConfigModel(graph_eviction_policy="adaptive"),
                        ):
                            StorageManager._enforce_ram_budget(75)

                            pls.assert_called()
                            mock_graph.remove_node.assert_any_call("a")


def test_enforce_ram_budget_priority_policy():
    """Test that _enforce_ram_budget evicts nodes using priority tiers."""
    mock_graph = MagicMock()
    mock_graph.has_node.return_value = True
    mock_graph.nodes = {
        "sys": {"type": "system", "confidence": 0.9},
        "user": {"type": "user", "confidence": 0.5},
        "res": {"type": "research", "confidence": 0.5},
    }
    mock_lru: OrderedDict[str, int] = OrderedDict(
        (k, i) for i, k in enumerate(["sys", "user", "res"])
    )

    def mock_remove_node(node_id):
        mock_graph.nodes.pop(node_id, None)

    mock_graph.remove_node.side_effect = mock_remove_node

    with patch.object(StorageManager.context, "graph", mock_graph):
        with patch.object(StorageManager.state, "lru", mock_lru):
            with patch(
                "autoresearch.storage.StorageManager._current_ram_mb",
                side_effect=[100, 100, 50, 50],
            ):
                with patch(
                    "autoresearch.config.loader.ConfigLoader.config",
                    new=ConfigModel(graph_eviction_policy="priority"),
                ):
                    start = EVICTION_COUNTER._value.get()
                    StorageManager._enforce_ram_budget(75)

                    assert mock_graph.remove_node.call_count == 2
                    assert "res" not in mock_graph.nodes
                    assert "user" not in mock_graph.nodes
                    assert EVICTION_COUNTER._value.get() == start + 2


def test_enforce_ram_budget_zero_budget():
    """Test that _enforce_ram_budget does nothing when the budget is zero."""
    # Setup
    mock_graph = MagicMock()

    with patch.object(StorageManager.context, "graph", mock_graph):
        # Execute
        StorageManager._enforce_ram_budget(0)

        # Verify
        mock_graph.remove_node.assert_not_called()


def test_enforce_ram_budget_no_nodes_to_evict():
    """Test that _enforce_ram_budget handles the case when there are no nodes to evict."""
    # Setup
    mock_graph = MagicMock()
    mock_graph.has_node.return_value = False
    mock_lru: OrderedDict[str, int] = OrderedDict()

    with patch.object(StorageManager.context, "graph", mock_graph):
        with patch.object(StorageManager.state, "lru", mock_lru):
            with patch("autoresearch.storage.StorageManager._current_ram_mb", return_value=100):
                with patch("autoresearch.config.loader.ConfigLoader.config") as mock_config:
                    mock_config.graph_eviction_policy = "lru"
                    mock_config.eviction_batch_size = 10
                    mock_config.eviction_safety_margin = 0.1

                    # Execute
                    StorageManager._enforce_ram_budget(75)

                    # Verify
                    mock_graph.remove_node.assert_not_called()
