# mypy: ignore-errors
# flake8: noqa
from tests.behavior.context import BehaviorContext
from unittest.mock import Mock
from pytest_bdd import scenario, given, when, then, parsers

from autoresearch import synthesis


@given(parsers.parse('a query "{query}" and five claims'))
def given_five_claims(query, bdd_context: BehaviorContext):
    bdd_context["query"] = query
    bdd_context["claims"] = [{"content": f"claim {i}"} for i in range(1, 6)]


@given(parsers.parse('a query "{query}" and no claims'))
def given_no_claims(query, bdd_context: BehaviorContext):
    bdd_context["query"] = query
    bdd_context["claims"] = []


@given("a long prompt and verbose claims")
def given_long_prompt(bdd_context: BehaviorContext):
    bdd_context["prompt"] = "one two three four five six seven"
    bdd_context["claims"] = [
        {"content": "one two three four"},
        {"content": "five six seven eight"},
        {"content": "nine ten eleven twelve"},
    ]


@when("I build the answer from the claims")
def build_answer_step(bdd_context: BehaviorContext, monkeypatch):
    monkeypatch.setattr(synthesis, "log", Mock())
    answer = synthesis.build_answer(bdd_context["query"], bdd_context["claims"])
    bdd_context["answer"] = answer


@when(parsers.parse("I compress the prompt to {budget:d} tokens"))
def compress_prompt_step(bdd_context: BehaviorContext, budget):
    compressed = synthesis.compress_prompt(bdd_context["prompt"], budget)
    bdd_context["compressed_prompt"] = compressed
    bdd_context["prompt_budget"] = budget


@when(parsers.parse("I compress the claims to {budget:d} tokens"))
def compress_claims_step(bdd_context: BehaviorContext, budget):
    compressed = synthesis.compress_claims(bdd_context["claims"], budget)
    bdd_context["compressed_claims"] = compressed
    bdd_context["claims_budget"] = budget


@then("the answer should include only the first three claims and the total count")
def check_concise_answer(bdd_context: BehaviorContext):
    answer = bdd_context["answer"]
    assert answer == "claim 1; claim 2; claim 3 ... (5 claims total)"
    assert "claim 4" not in answer
    assert "claim 5" not in answer


@then(parsers.parse('the answer should be "{expected}"'))
def check_exact_answer(bdd_context: BehaviorContext, expected):
    answer = bdd_context["answer"]
    assert answer == expected
    assert len(answer.split()) == len(expected.split())


@then(parsers.parse("the answer token count should be {count:d}"))
def check_answer_tokens(bdd_context: BehaviorContext, count):
    answer = bdd_context["answer"]
    assert len(answer.split()) == count


@then("the compressed prompt should be within the token budget and contain an ellipsis")
def check_compressed_prompt(bdd_context: BehaviorContext):
    compressed = bdd_context["compressed_prompt"]
    budget = bdd_context["prompt_budget"]
    assert len(compressed.split()) <= budget
    assert "..." in compressed
    assert compressed == "one two ... six seven"


@then("the compressed claims should fit within the token budget with truncation")
def check_compressed_claims(bdd_context: BehaviorContext):
    compressed = bdd_context["compressed_claims"]
    budget = bdd_context["claims_budget"]
    total_tokens = sum(len(c["content"].split()) for c in compressed)
    assert total_tokens <= budget
    assert compressed[-1]["content"].endswith("...")
    assert compressed[0]["content"] == "one two three four"
    assert compressed[1]["content"] == "five six seven eight"
    assert len(compressed) == 3


@scenario("../features/synthesis.feature", "Generating concise answers from more than three claims")
def test_concise_answer():
    pass


@scenario("../features/synthesis.feature", "Producing no answer when claims list is empty")
def test_no_answer():
    pass


@scenario("../features/synthesis.feature", "Compressing prompts and claims when token budget is exceeded")
def test_compression():
    pass
