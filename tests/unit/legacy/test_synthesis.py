# mypy: ignore-errors
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


def test_build_answer_empty_claims() -> None:
    """Test build_answer with empty claims list."""
    answer = build_answer("test query", [])
    assert answer == "No answer found for 'test query'."


def test_build_answer_many_claims() -> None:
    """Test build_answer with more than 3 claims."""
    claims = [
        {"content": "first claim"},
        {"content": "second claim"},
        {"content": "third claim"},
        {"content": "fourth claim"},
        {"content": "fifth claim"},
    ]
    typed_claims = cast(list[dict[str, str]], claims)
    answer = build_answer("query", typed_claims)
    assert "first claim" in answer
    assert "second claim" in answer
    assert "third claim" in answer
    assert "(5 claims total)" in answer


def test_build_rationale_empty_claims() -> None:
    """Test build_rationale with empty claims list."""
    rationale = build_rationale([])
    assert rationale == "No rationale available."


def test_compress_prompt_no_compression() -> None:
    """Test compress_prompt when no compression is needed."""
    from autoresearch.synthesis import compress_prompt

    prompt = "short prompt"
    result = compress_prompt(prompt, 10)
    assert result == prompt


def test_compress_prompt_with_compression() -> None:
    """Test compress_prompt when compression is needed."""
    from autoresearch.synthesis import compress_prompt

    prompt = "this is a very long prompt that should be compressed to fit within the token budget"
    result = compress_prompt(prompt, 5)
    tokens = result.split()
    assert len(tokens) <= 5 + 1  # +1 for the "..." token
    assert "..." in result
    assert result.startswith("this")
    assert result.endswith("budget")


def test_compress_claims_no_compression() -> None:
    """Test compress_claims when no compression is needed."""
    from autoresearch.synthesis import compress_claims

    claims = [
        {"content": "short claim"},
        {"content": "another short claim"},
    ]
    result = compress_claims(claims, 10)
    assert result == claims


def test_compress_claims_with_compression() -> None:
    """Test compress_claims when compression is needed."""
    from autoresearch.synthesis import compress_claims

    claims = [
        {"content": "this is a long claim that will exceed the budget"},
        {"content": "another claim"},
    ]
    result = compress_claims(claims, 5)
    assert len(result) == 1
    assert "..." in result[0]["content"]
    assert result[0]["content"].startswith("this")
