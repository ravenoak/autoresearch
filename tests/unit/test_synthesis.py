from autoresearch.synthesis import build_answer, build_rationale


def test_build_answer_and_rationale():
    claims = [{"content": "first"}, {"content": "second"}]
    answer = build_answer("query", claims)
    rationale = build_rationale(claims)

    assert "first" in answer and "second" in answer
    assert "- first" in rationale and "- second" in rationale
