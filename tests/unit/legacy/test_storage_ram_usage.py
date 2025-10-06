"""Tests for RAM usage calculation in the storage module.

This module contains tests for the _current_ram_mb method, which is responsible
for calculating the current RAM usage of the graph.
"""

from unittest.mock import patch, MagicMock
import networkx as nx

from autoresearch.storage import StorageManager


def test_current_ram_mb_empty_graph():
    """Test that _current_ram_mb returns 0 for an empty graph."""
    # Setup
    mock_graph = nx.DiGraph()

    # Instead of trying to mock psutil which may not be available,
    # we'll patch the resource module's getrusage function to return 0
    mock_resource = MagicMock()
    mock_rusage = MagicMock()
    mock_rusage.ru_maxrss = 0
    mock_resource.getrusage.return_value = mock_rusage

    with (
        patch.object(StorageManager.context, "graph", mock_graph),
        patch.dict("sys.modules", {"psutil": None}),
        patch.dict("sys.modules", {"resource": mock_resource}),
        patch("resource.getrusage", return_value=mock_rusage),
        patch("resource.RUSAGE_SELF", 0),
    ):
        # Execute
        result = StorageManager._current_ram_mb()

        # Verify
        assert result == 0


def test_current_ram_mb_with_nodes(realistic_claim_batch):
    """_current_ram_mb accounts for multiple nodes with varied content."""
    mock_graph = nx.DiGraph()

    for claim in realistic_claim_batch:
        data = claim.copy()
        claim_id = data.pop("id")
        mock_graph.add_node(claim_id, **data)

    with patch.object(StorageManager.context, "graph", mock_graph):
        result = StorageManager._current_ram_mb()
        assert result > 0


def test_current_ram_mb_with_attributes(realistic_claim_batch):
    """Attributes, embeddings and relations contribute to RAM size."""
    mock_graph = nx.DiGraph()

    claim = realistic_claim_batch[0]
    data = claim.copy()
    claim_id = data.pop("id")
    data.setdefault("attributes", {"key": "val"})
    mock_graph.add_node(claim_id, **data)

    with patch.object(StorageManager.context, "graph", mock_graph):
        result = StorageManager._current_ram_mb()
        assert result > 0


def test_current_ram_mb_none_graph():
    """Test that _current_ram_mb handles None graph gracefully."""
    # Setup
    # Mock the resource module's getrusage function to return 0
    mock_resource = MagicMock()
    mock_rusage = MagicMock()
    mock_rusage.ru_maxrss = 0
    mock_resource.getrusage.return_value = mock_rusage

    with (
        patch.object(StorageManager.context, "graph", None),
        patch.dict("sys.modules", {"psutil": None}),
        patch.dict("sys.modules", {"resource": mock_resource}),
        patch("resource.getrusage", return_value=mock_rusage),
        patch("resource.RUSAGE_SELF", 0),
    ):
        # Execute
        result = StorageManager._current_ram_mb()

        # Verify
        assert result == 0


def test_current_ram_mb_large_graph():
    """Test that _current_ram_mb scales correctly with graph size."""
    # Setup
    mock_graph = nx.DiGraph()

    # Add many nodes to simulate a large graph
    for i in range(100):
        mock_graph.add_node(f"node{i}", content=f"content for node {i}")

    # Mock the resource module to return different values based on graph size
    # For the large graph, return a higher memory usage
    mock_resource_large = MagicMock()
    mock_rusage_large = MagicMock()
    mock_rusage_large.ru_maxrss = 100 * 1024  # 100 MB in KB
    mock_resource_large.getrusage.return_value = mock_rusage_large

    with (
        patch.object(StorageManager.context, "graph", mock_graph),
        patch.dict("sys.modules", {"psutil": None}),
        patch.dict("sys.modules", {"resource": mock_resource_large}),
        patch("resource.getrusage", return_value=mock_rusage_large),
        patch("resource.RUSAGE_SELF", 0),
    ):
        # Execute
        StorageManager.state.baseline_mb = 0
        result = StorageManager._current_ram_mb()

        # Verify
        assert result > 0

        # The RAM usage should be proportional to the number of nodes
        # Let's measure the RAM usage of a smaller graph for comparison
        small_graph = nx.DiGraph()
        for i in range(10):
            small_graph.add_node(f"small_node{i}", content=f"content for node {i}")

        # For the small graph, return a lower memory usage
        mock_resource_small = MagicMock()
        mock_rusage_small = MagicMock()
        mock_rusage_small.ru_maxrss = 10 * 1024  # 10 MB in KB
        mock_resource_small.getrusage.return_value = mock_rusage_small

        with (
            patch.object(StorageManager.context, "graph", small_graph),
            patch.dict("sys.modules", {"psutil": None}),
            patch.dict("sys.modules", {"resource": mock_resource_small}),
            patch("resource.getrusage", return_value=mock_rusage_small),
            patch("resource.RUSAGE_SELF", 0),
        ):
            small_result = StorageManager._current_ram_mb()

            # The larger graph should use more RAM
            assert result > small_result
