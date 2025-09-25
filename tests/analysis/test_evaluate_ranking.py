from importlib import util
from pathlib import Path

import pytest

from tests.optional_imports import import_or_skip

pytestmark = pytest.mark.requires_parsers

# Skip if optional parsers are unavailable
import_or_skip("docx")
import_or_skip("pdfminer.high_level")

spec = util.spec_from_file_location(
    "evaluate_ranking",
    Path(__file__).resolve().parents[2] / "scripts" / "evaluate_ranking.py",
)
if spec is None or spec.loader is None:
    raise RuntimeError("Unable to load evaluate_ranking module")
module = util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_evaluate_ranking_zero_metrics() -> None:
    data_path = Path(__file__).resolve().parents[1] / "data" / "eval" / "sample_eval.csv"
    data = module.load_data(data_path)
    precision, recall = module.evaluate(data, (0.5, 0.3, 0.2))
    assert precision == 0.0
    assert recall == 0.0
