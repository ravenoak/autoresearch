"""Benchmark regression for token usage, memory, and latency."""

from __future__ import annotations

import sys
import types

import pytest

pdf_ns = types.SimpleNamespace(extract_text=lambda *a, **k: "")
sys.modules.setdefault("docx", types.SimpleNamespace(Document=object))
sys.modules.setdefault("pdfminer", types.SimpleNamespace(high_level=pdf_ns))
sys.modules.setdefault("pdfminer.high_level", pdf_ns)

from scripts.benchmark_token_memory import run_benchmark

pytestmark = [pytest.mark.slow]


def test_token_memory_baseline(token_memory_baseline) -> None:
    """Check token, memory, and duration metrics against baselines."""
    metrics = run_benchmark()
    tokens = metrics["tokens"]["Dummy"]
    token_memory_baseline(
        tokens["in"],
        tokens["out"],
        metrics["memory_delta_mb"],
        metrics["duration_seconds"],
    )
