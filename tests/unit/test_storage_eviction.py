from collections import OrderedDict
from unittest.mock import MagicMock, patch

from autoresearch.orchestration.metrics import EVICTION_COUNTER
from autoresearch.storage import StorageManager


def test_pop_lru():
    """Test that _pop_lru removes and returns the least recently used node."""
    # Setup
    mock_lru = OrderedDict([("a", 1), ("b", 2), ("c", 3)])
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
    mock_lru = OrderedDict()
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
    mock_lru = OrderedDict([("a", 1), ("b", 2), ("c", 3)])

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
    mock_lru = OrderedDict((str(i), i) for i in range(10))

    with patch.object(StorageManager.context, "graph", mock_graph):
        with patch.object(StorageManager.state, "lru", mock_lru):
            with patch(
                "autoresearch.storage.StorageManager._current_ram_mb",
                side_effect=[100, 100, 100, 50, 50],
            ):
                with patch("autoresearch.config.loader.ConfigLoader.config") as mock_config:
                    mock_config.graph_eviction_policy = "lru"
                    mock_config.eviction_batch_size = 10

                # Execute
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
    mock_lru = OrderedDict((str(i), i) for i in range(10))

    # Set up the remove_node method to update the nodes dictionary
    def mock_remove_node(node_id):
        nodes_dict.pop(node_id, None)

    mock_graph.remove_node.side_effect = mock_remove_node

    with patch.object(StorageManager.context, "graph", mock_graph):
        with patch.object(StorageManager.state, "lru", mock_lru):
            with patch(
                "autoresearch.storage.StorageManager._current_ram_mb",
                side_effect=[100, 100, 100, 50, 50],
            ):
                with patch("autoresearch.config.loader.ConfigLoader.config") as mock_config:
                    mock_config.graph_eviction_policy = "score"
                    mock_config.eviction_batch_size = 10
                    mock_config.eviction_safety_margin = 0.1

                # Execute
                start = EVICTION_COUNTER._value.get()
                StorageManager._enforce_ram_budget(75)

                # Verify
                assert mock_graph.remove_node.call_count == 2
                mock_graph.remove_node.assert_any_call("0")
                mock_graph.remove_node.assert_any_call("1")
                assert EVICTION_COUNTER._value.get() == start + 2

                # Verify that remaining nodes exclude evicted ones
                assert "0" not in nodes_dict and "1" not in nodes_dict


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
    mock_lru = OrderedDict()

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
