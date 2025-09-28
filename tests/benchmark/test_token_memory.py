"""Benchmark regression for token usage, memory, and latency."""

from __future__ import annotations

from typing import cast

import pytest

from tests.helpers.modules import ensure_stub_module

ensure_stub_module("docx", {"Document": object})
ensure_stub_module(
    "pdfminer.high_level", {"extract_text": lambda *a, **k: ""}
)

from scripts.benchmark_token_memory import run_benchmark  # noqa: E402

pytestmark = [pytest.mark.slow]


def test_token_memory_baseline(token_memory_baseline) -> None:
    """Check token, memory, and duration metrics against baselines."""
    metrics = run_benchmark()
    token_map = cast(dict[str, dict[str, int]], metrics["tokens"])
    tokens = token_map["Dummy"]
    token_memory_baseline(
        tokens["in"],
        tokens["out"],
        metrics["memory_delta_mb"],
        metrics["duration_seconds"],
    )
