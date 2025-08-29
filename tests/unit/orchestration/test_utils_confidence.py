import autoresearch.orchestration.utils as utils
from autoresearch.models import QueryResponse


def test_calculate_confidence_rewards_signal() -> None:
    resp = QueryResponse(
        answer="",
        citations=[{"id": i} for i in range(3)],
        reasoning=["r"] * 10,
        metrics={"token_usage": {"total": 30, "max_tokens": 50}},
    )
    score = utils.calculate_result_confidence(resp)
    assert score == 0.85


def test_calculate_confidence_penalties() -> None:
    resp = QueryResponse(
        answer="",
        citations=[],
        reasoning=[],
        metrics={
            "token_usage": {"total": 100, "max_tokens": 50},
            "errors": [1, 2],
        },
    )
    score = utils.calculate_result_confidence(resp)
    assert score == 0.2
