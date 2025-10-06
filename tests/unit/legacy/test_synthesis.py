from __future__ import annotations

from typing import TypedDict, cast

from autoresearch.synthesis import build_answer, build_rationale


class ClaimDict(TypedDict):
    """Structure of claims used by synthesis helpers."""

    content: str


def test_build_answer_and_rationale() -> None:
    claims: list[ClaimDict] = [{"content": "first"}, {"content": "second"}]
    typed_claims = cast(list[dict[str, str]], claims)
    answer = build_answer("query", typed_claims)
    rationale = build_rationale(typed_claims)

    assert "first" in answer and "second" in answer
    assert "- first" in rationale and "- second" in rationale
