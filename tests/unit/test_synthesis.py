from autoresearch.synthesis import build_answer, build_rationale


def test_build_answer_and_rationale():
    claims = [{"content": "a"}, {"content": "b"}]
    answer = build_answer("query", claims)
    rationale = build_rationale(claims)
    assert "2" in answer
    assert "2" in rationale
