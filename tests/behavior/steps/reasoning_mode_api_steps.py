from __future__ import annotations
from tests.behavior.utils import as_payload
from typing import Any

import asyncio
from unittest.mock import patch

from pytest_bdd import given, parsers, scenario, then, when

from autoresearch.config.loader import ConfigLoader
from autoresearch.config.models import ConfigModel
from autoresearch.orchestration import ReasoningMode
from autoresearch.orchestration.orchestrator import Orchestrator


@scenario("../features/reasoning_mode_api.feature", "Direct mode via API")
def test_direct_mode_api():
    pass


@scenario("../features/reasoning_mode_api.feature", "Chain-of-thought mode via API")
def test_chain_of_thought_mode_api():
    pass


@scenario("../features/reasoning_mode_api.feature", "Dialectical mode via API")
def test_dialectical_mode_api():
    pass


@scenario("../features/reasoning_mode_api.feature", "Direct mode via async API")
def test_direct_mode_async_api():
    pass


@scenario(
    "../features/reasoning_mode_api.feature",
    "Chain-of-thought mode via async API",
)
def test_cot_mode_async_api():
    pass


@scenario("../features/reasoning_mode_api.feature", "Dialectical mode via async API")
def test_dialectical_mode_async_api():
    pass


@scenario(
    "../features/reasoning_mode_api.feature",
    "Mode switching within a session via API",
)
def test_mode_switch_api():
    pass


@scenario(
    "../features/reasoning_mode_api.feature",
    "Invalid reasoning mode via API",
)
def test_invalid_mode_api():
    pass


@given("the API server is running", target_fixture="test_context")
def api_server_running(api_client):
    return as_payload({"client": api_client})


@given(
    parsers.parse("loops is set to {count:d} in configuration"), target_fixture="config"
)
def loops_config(count: int, monkeypatch):
    cfg = ConfigModel(agents=["Synthesizer", "Contrarian", "FactChecker"], loops=count)
    monkeypatch.setattr(ConfigLoader, "load_config", lambda self: cfg)
    return cfg


@when(
    parsers.parse('I send a query "{query}" with reasoning mode "{mode}" to the API'),
    target_fixture="run_result",
)
def send_query(test_context: dict, query: str, mode: str, config: ConfigModel):
    record: list[str] = []
    params: dict[str, Any] = {}
    logs: list[str] = []
    state = {"active": True}

    class DummyAgent:
        def __init__(self, name: str) -> None:
            self.name = name

        def can_execute(self, *args, **kwargs) -> bool:
            return True

        def execute(self, *args, **kwargs) -> dict:
            step = len(record) + 1
            record.append(self.name)
            content = f"{self.name}-{step}"
            return as_payload({
                "claims": [
                    {
                        "id": str(step),
                        "type": "thought",
                        "content": content,
                    }
                ],
                "results": {"final_answer": content},
            })

    def get_agent(name: str) -> DummyAgent:
        return DummyAgent(name)

    original_parse = Orchestrator._parse_config

    def spy_parse(cfg: ConfigModel):
        out = original_parse(cfg)
        params.update(out)
        return out

    with (
        patch(
            "autoresearch.orchestration.orchestrator.AgentFactory.get",
            side_effect=get_agent,
        ),
        patch(
            "autoresearch.orchestration.orchestrator.Orchestrator._parse_config",
            side_effect=spy_parse,
        ),
    ):
        response = test_context["client"].post(
            "/query", json={"query": query, "reasoning_mode": mode}
        )
        if response.status_code != 200:
            logs.append("unsupported reasoning mode")
    state["active"] = False
    data: dict[str, Any] = {}
    try:
        data = response.json()
    except Exception:
        data: dict[str, Any] = {}
    test_context["response"] = response
    return as_payload({
        "record": record,
        "config_params": params,
        "data": data,
        "logs": logs,
        "state": state,
    })


@when(
    parsers.parse(
        'I send an async query "{query}" with reasoning mode "{mode}" to the API'
    ),
    target_fixture="run_result",
)
def send_async_query(test_context: dict, query: str, mode: str, config: ConfigModel):
    record: list[str] = []
    params: dict[str, Any] = {}
    logs: list[str] = []
    state = {"active": True}

    class DummyAgent:
        def __init__(self, name: str) -> None:
            self.name = name

        def can_execute(self, *args, **kwargs) -> bool:
            return True

        def execute(self, *args, **kwargs) -> dict:
            step = len(record) + 1
            record.append(self.name)
            content = f"{self.name}-{step}"
            return as_payload({
                "claims": [
                    {
                        "id": str(step),
                        "type": "thought",
                        "content": content,
                    }
                ],
                "results": {"final_answer": content},
            })

    def get_agent(name: str) -> DummyAgent:
        return DummyAgent(name)

    original_parse = Orchestrator._parse_config

    def spy_parse(cfg: ConfigModel):
        out = original_parse(cfg)
        params.update(out)
        return out

    async def run_async(self, q: str, cfg: ConfigModel, callbacks=None, **kwargs):
        return self.run_query(q, cfg)

    with (
        patch(
            "autoresearch.orchestration.orchestrator.AgentFactory.get",
            side_effect=get_agent,
        ),
        patch(
            "autoresearch.orchestration.orchestrator.Orchestrator._parse_config",
            side_effect=spy_parse,
        ),
        patch(
            "autoresearch.orchestration.orchestrator.Orchestrator.run_query_async",
            side_effect=run_async,
        ),
    ):
        client = test_context["client"]
        submit = client.post(
            "/query/async", json={"query": query, "reasoning_mode": mode}
        )
        if submit.status_code != 200:
            logs.append("unsupported reasoning mode")
            test_context["response"] = submit
            state["active"] = False
            return as_payload({
                "record": record,
                "config_params": params,
                "data": {},
                "logs": logs,
                "state": state,
            })
        query_id = submit.json()["query_id"]
        task = client.app.state.async_tasks.get(query_id)
        assert isinstance(task, asyncio.Task)
        while not task.done():
            pass
        response = client.get(f"/query/{query_id}")
    state["active"] = False
    data: dict[str, Any] = {}
    try:
        data = response.json()
    except Exception:
        data: dict[str, Any] = {}
    test_context["response"] = response
    return as_payload({
        "record": record,
        "config_params": params,
        "data": data,
        "logs": logs,
        "state": state,
    })


@then(parsers.parse("the response status should be {status:d}"))
def assert_status(test_context: dict, status: int) -> None:
    resp = test_context["response"]
    assert resp.status_code == status
    data: dict[str, Any] = {}
    try:
        data = resp.json()
    except Exception:
        pass
    if status == 200:
        assert "error" not in data
    else:
        assert "error" in data or "detail" in data


@then(parsers.parse("the loops used should be {count:d}"))
def assert_loops(run_result: dict, count: int) -> None:
    assert run_result["config_params"].get("loops") == count


@then(parsers.parse('the reasoning mode selected should be "{mode}"'))
def assert_mode(run_result: dict, mode: str) -> None:
    assert run_result["config_params"].get("mode") == ReasoningMode(mode)


@then(parsers.parse('the agent groups should be "{groups}"'))
def assert_groups(run_result: dict, groups: str) -> None:
    expected = [
        [a.strip() for a in grp.split(",") if a.strip()] for grp in groups.split(";")
    ]
    assert run_result["config_params"].get("agent_groups") == expected


@then(parsers.parse('the agents executed should be "{order}"'))
def assert_order(run_result: dict, order: str) -> None:
    expected = [a.strip() for a in order.split(",")]
    assert run_result["record"] == expected


@then(parsers.parse('the reasoning steps should be "{steps}"'))
def assert_reasoning(run_result: dict, steps: str) -> None:
    expected = [s.strip() for s in steps.split(";") if s.strip()]
    actual = [c.get("content") for c in run_result["data"].get("reasoning", [])]
    assert actual == expected


@then(parsers.parse("the metrics should record {count:d} cycles"))
def assert_metrics_cycles(run_result: dict, count: int) -> None:
    metrics = run_result["data"].get("metrics", {}).get("execution_metrics", {})
    assert metrics.get("cycles_completed") == count


@then(parsers.parse('the metrics should list agents "{agents}"'))
def assert_metrics_agents(run_result: dict, agents: str) -> None:
    expected = [a.strip() for a in agents.split(",") if a.strip()]
    metrics = run_result["data"].get("metrics", {}).get("execution_metrics", {})
    actual = list(metrics.get("agent_timings", {}).keys())
    assert actual == expected


@then("a reasoning mode error should be returned")
def assert_reasoning_mode_error(test_context: dict) -> None:
    data: dict[str, Any] = {}
    try:
        data = test_context["response"].json()
    except Exception:
        pass
    assert "reasoning" in str(data).lower() or "mode" in str(data).lower()


@then("no agents should execute")
def assert_no_agents(run_result: dict) -> None:
    assert run_result["record"] == []
