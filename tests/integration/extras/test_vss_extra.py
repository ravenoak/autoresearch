# mypy: ignore-errors
"""Tests for the VSS optional extra."""

from __future__ import annotations

import duckdb
import pytest

from autoresearch.extensions import VSSExtensionLoader


@pytest.mark.requires_vss
def test_vss_extension_loader() -> None:
    """The VSS extra enables DuckDB vector extension management."""
    conn = duckdb.connect(":memory:")
    if VSSExtensionLoader.verify_extension(conn, verbose=False):
        pytest.skip("VSS extension already loaded")
    assert VSSExtensionLoader.verify_extension(conn, verbose=False) is False
