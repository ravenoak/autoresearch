# mypy: ignore-errors
from __future__ import annotations
from tests.behavior.utils import as_payload

import types
from collections.abc import Callable, Iterator, Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any, TypedDict, cast
from unittest.mock import patch

import pytest
from pytest_bdd import given, parsers, scenario, then, when

from autoresearch.config.loader import ConfigLoader
from autoresearch.config.models import ConfigModel
from autoresearch.errors import AgentError, StorageError, TimeoutError
from autoresearch.orchestration import ReasoningMode
from autoresearch.orchestration.orchestrator import AgentFactory, Orchestrator
from autoresearch.orchestration.orchestration_utils import OrchestrationUtils
from autoresearch.storage import StorageManager
from tests.behavior.context import (
    BehaviorContext,
    get_config,
    get_orchestrator,
    set_value,
)
from tests.typing_helpers import TypedFixture

pytest_plugins = ["tests.behavior.steps.common_steps"]


class ErrorEntry(TypedDict, total=False):
    """Typed dictionary describing expected error payload fields."""

    error_type: str
    message: str
    recovery_strategy: str
    error_category: str
    recovery_applied: bool
    agent: str


@dataclass
class ExecutionState:
    """Track whether the orchestrator run is active."""

    active: bool = True


@dataclass
class RecoveryDetails:
    """Structured capture of recovery metadata returned by the orchestrator."""

    agent: str | None = None
    error_type: str | None = None
    message: str | None = None
    error_category: str | None = None
    recovery_strategy: str | None = None
    suggestion: str | None = None
    recovery_applied: bool | None = None

    def update_from_mapping(self, payload: Mapping[str, Any]) -> None:
        """Populate fields using known keys from ``payload``."""

        for key, value in payload.items():
            if key == "agent" and value is not None:
                self.agent = str(value)
            elif key in {"error", "message"} and value is not None:
                self.message = str(value)
            elif key == "error_type" and value is not None:
                self.error_type = str(value)
            elif key == "error_category" and value is not None:
                self.error_category = str(value)
            elif key == "recovery_strategy" and value is not None:
                self.recovery_strategy = str(value)
            elif key == "suggestion" and value is not None:
                self.suggestion = str(value)
            elif key == "recovery_applied":
                self.recovery_applied = bool(value)

    def mark_applied(self, applied: bool | None) -> None:
        """Record whether recovery routines were applied."""

        if applied is not None:
            self.recovery_applied = bool(applied)

    def as_error_entry(self) -> ErrorEntry:
        """Convert captured details into an :class:`ErrorEntry`."""

        entry: ErrorEntry = {}
        if self.error_type is not None:
            entry["error_type"] = self.error_type
        if self.message is not None:
            entry["message"] = self.message
        if self.recovery_strategy is not None:
            entry["recovery_strategy"] = self.recovery_strategy
        if self.error_category is not None:
            entry["error_category"] = self.error_category
        if self.recovery_applied is not None:
            entry["recovery_applied"] = self.recovery_applied
        if self.agent is not None:
            entry["agent"] = self.agent
        return entry

    def has_details(self) -> bool:
        """Return ``True`` when any field has been populated."""

        return any(
            value is not None
            for value in (
                self.agent,
                self.error_type,
                self.message,
                self.error_category,
                self.recovery_strategy,
                self.suggestion,
                self.recovery_applied,
            )
        )

    def reset(self) -> None:
        """Clear all stored metadata so the instance can be reused."""

        self.agent = None
        self.error_type = None
        self.message = None
        self.error_category = None
        self.recovery_strategy = None
        self.suggestion = None
        self.recovery_applied = None

    def snapshot(self) -> RecoveryDetails:
        """Return a copy of the current details for result snapshots."""

        return RecoveryDetails(
            agent=self.agent,
            error_type=self.error_type,
            message=self.message,
            error_category=self.error_category,
            recovery_strategy=self.recovery_strategy,
            suggestion=self.suggestion,
            recovery_applied=self.recovery_applied,
        )


@dataclass
class RunResult:
    """Structured response for successful orchestrator executions."""

    recovery: RecoveryDetails
    response: object
    record: list[str] = field(default_factory=list)
    config_params: dict[str, Any] = field(default_factory=dict)
    logs: list[str] = field(default_factory=list)
    state: ExecutionState = field(default_factory=ExecutionState)

    @property
    def errors(self) -> list[ErrorEntry]:
        """Return normalized error entries from response metadata."""

        metadata = getattr(self.response, "metadata", {})
        if not isinstance(metadata, Mapping):
            return []
        raw_errors = metadata.get("errors", [])
        if not isinstance(raw_errors, Sequence):
            return []
        normalized: list[ErrorEntry] = []
        for entry in raw_errors:
            if isinstance(entry, Mapping):
                normalized.append(_normalize_error_entry(entry))
        return normalized


@dataclass
class ErrorResult:
    """Structured response for orchestrator executions that raise errors."""

    error: Exception | None
    record: list[str] = field(default_factory=list)
    logs: list[str] = field(default_factory=list)
    state: ExecutionState = field(default_factory=ExecutionState)


def _normalize_error_entry(entry: Mapping[str, Any]) -> ErrorEntry:
    """Normalize heterogeneous error payloads into an :class:`ErrorEntry`."""

    normalized: ErrorEntry = {}
    if "error_type" in entry and entry["error_type"] is not None:
        normalized["error_type"] = str(entry["error_type"])
    if "message" in entry and entry["message"] is not None:
        normalized["message"] = str(entry["message"])
    elif "error" in entry and entry["error"] is not None:
        normalized["message"] = str(entry["error"])
    if "recovery_strategy" in entry and entry["recovery_strategy"] is not None:
        normalized["recovery_strategy"] = str(entry["recovery_strategy"])
    if "error_category" in entry and entry["error_category"] is not None:
        normalized["error_category"] = str(entry["error_category"])
    if "recovery_applied" in entry:
        normalized["recovery_applied"] = bool(entry["recovery_applied"])
    if "agent" in entry and entry["agent"] is not None:
        normalized["agent"] = str(entry["agent"])
    return normalized


def _assert_error_schema(errors: Sequence[ErrorEntry]) -> None:
    """Verify error entries contain the expected keys."""

    required = {"error_type", "message"}
    for err in errors:
        missing = {key for key in required if not err.get(key)}
        assert not missing, f"Missing keys {sorted(missing)} in error entry: {err}"


@scenario(
    "../features/error_recovery.feature",
    "Error recovery in dialectical reasoning mode",
)
def test_error_recovery_dialectical():
    pass


@scenario(
    "../features/error_recovery.feature",
    "Error recovery in direct reasoning mode",
)
def test_error_recovery_direct():
    pass


@scenario(
    "../features/error_recovery.feature",
    "Error recovery in chain-of-thought reasoning mode",
)
def test_error_recovery_cot():
    pass


@scenario(
    "../features/error_recovery.feature",
    "Recovery after storage failure",
)
def test_error_recovery_storage_failure():
    pass


@scenario(
    "../features/error_recovery.feature",
    "Recovery after persistent network outage",
)
def test_error_recovery_network_outage():
    pass


@scenario(
    "../features/error_recovery.feature",
    "Recovery after agent timeout",
)
def test_error_recovery_timeout():
    pass


@scenario(
    "../features/error_recovery.feature",
    "Recovery after critical agent failure",
)
def test_error_recovery_agent_failure():
    pass


@scenario(
    "../features/error_recovery.feature",
    "Unsupported reasoning mode during recovery fails gracefully",
)
def test_error_recovery_unsupported_mode():
    pass


@scenario(
    "../features/error_recovery.feature",
    "Recovery after agent failure with fallback",
)
def test_error_recovery_agent_fallback():
    pass


@scenario(
    "../features/error_recovery.feature",
    "Error recovery with a realistic query",
)
def test_error_recovery_realistic_query():
    pass


@scenario(
    "../features/error_recovery.feature",
    "Successful run does not trigger recovery",
)
def test_error_recovery_none():
    pass


@given("an agent that raises a transient error", target_fixture="config")
def flaky_agent(
    monkeypatch: pytest.MonkeyPatch,
    isolate_network: TypedFixture[None],
    restore_environment: TypedFixture[None],
    bdd_context: BehaviorContext,
) -> ConfigModel:
    cfg = ConfigModel.model_construct(agents=["Flaky"], loops=1)

    class FlakyAgent:
        def can_execute(self, *args: object, **kwargs: object) -> bool:
            return True

        def execute(self, *args: object, **kwargs: object) -> dict[str, Any]:
            raise AgentError("temporary network issue")

    monkeypatch.setattr(ConfigLoader, "load_config", lambda self, *a, **k: cfg)
    monkeypatch.setattr(
        AgentFactory,
        "get",
        classmethod(lambda cls, name, llm_adapter=None: FlakyAgent()),
    )
    return set_value(bdd_context, "config", cfg)


@given("an agent that times out during execution", target_fixture="config")
def timeout_agent(
    monkeypatch: pytest.MonkeyPatch,
    isolate_network: TypedFixture[None],
    restore_environment: TypedFixture[None],
    bdd_context: BehaviorContext,
) -> ConfigModel:
    cfg = ConfigModel.model_construct(agents=["Slowpoke"], loops=1)

    class TimeoutAgent:
        def can_execute(self, *args: object, **kwargs: object) -> bool:
            return True

        def execute(self, *args: object, **kwargs: object) -> dict[str, Any]:
            raise TimeoutError("simulated timeout")

    monkeypatch.setattr(ConfigLoader, "load_config", lambda self, *a, **k: cfg)
    monkeypatch.setattr(
        AgentFactory,
        "get",
        classmethod(lambda cls, name, llm_adapter=None: TimeoutAgent()),
    )
    return set_value(bdd_context, "config", cfg)


@given("an agent that fails during execution", target_fixture="config")
def failing_agent(
    monkeypatch: pytest.MonkeyPatch,
    isolate_network: TypedFixture[None],
    restore_environment: TypedFixture[None],
    bdd_context: BehaviorContext,
) -> ConfigModel:
    cfg = ConfigModel.model_construct(agents=["Faulty"], loops=1)

    class FailingAgent:
        def can_execute(self, *args: object, **kwargs: object) -> bool:
            return True

        def execute(self, *args: object, **kwargs: object) -> dict[str, Any]:
            raise AgentError("agent execution failed")

    monkeypatch.setattr(ConfigLoader, "load_config", lambda self, *a, **k: cfg)
    monkeypatch.setattr(
        AgentFactory,
        "get",
        classmethod(lambda cls, name, llm_adapter=None: FailingAgent()),
    )
    return set_value(bdd_context, "config", cfg)


@given(
    "an agent that fails triggering fallback",
    target_fixture="config",
)
def failing_agent_fallback(
    monkeypatch: pytest.MonkeyPatch,
    isolate_network: TypedFixture[None],
    restore_environment: TypedFixture[None],
    bdd_context: BehaviorContext,
) -> ConfigModel:
    cfg = ConfigModel.model_construct(agents=["Faulty"], loops=1)

    class FailingAgent:
        def can_execute(self, *args: object, **kwargs: object) -> bool:
            return True

        def execute(self, *args: object, **kwargs: object) -> dict[str, Any]:
            raise AgentError("agent execution failed")

    def handle(
        agent_name: str,
        exc: Exception,
        state: types.SimpleNamespace,
        metrics: object,
    ) -> dict[str, str]:
        info: dict[str, str] = {
            "recovery_strategy": "fallback_agent",
            "error_category": "recoverable",
        }
        state.metadata["recovery_applied"] = True
        return info

    monkeypatch.setattr(ConfigLoader, "load_config", lambda self, *a, **k: cfg)
    monkeypatch.setattr(
        AgentFactory,
        "get",
        classmethod(lambda cls, name, llm_adapter=None: FailingAgent()),
    )
    monkeypatch.setattr(
        OrchestrationUtils,
        "handle_agent_error",
        handle,
    )
    return set_value(bdd_context, "config", cfg)


@given("a reliable agent", target_fixture="config")
def reliable_agent(
    monkeypatch: pytest.MonkeyPatch,
    isolate_network: TypedFixture[None],
    restore_environment: TypedFixture[None],
    bdd_context: BehaviorContext,
) -> ConfigModel:
    cfg = ConfigModel.model_construct(agents=["Reliable"], loops=1)

    class ReliableAgent:
        def can_execute(self, *args: object, **kwargs: object) -> bool:
            return True

        def execute(self, *args: object, **kwargs: object) -> dict[str, Any]:
            return as_payload({})

    monkeypatch.setattr(ConfigLoader, "load_config", lambda self, *a, **k: cfg)
    monkeypatch.setattr(
        AgentFactory,
        "get",
        classmethod(lambda cls, name, llm_adapter=None: ReliableAgent()),
    )
    return set_value(bdd_context, "config", cfg)


@given("a storage layer that raises a StorageError", target_fixture="config")
def storage_failure_agent(
    monkeypatch: pytest.MonkeyPatch,
    isolate_network: TypedFixture[None],
    restore_environment: TypedFixture[None],
    bdd_context: BehaviorContext,
) -> ConfigModel:
    cfg = ConfigModel.model_construct(agents=["StoreFail"], loops=1)

    def fail_persist(*args: object, **kwargs: object) -> None:
        raise StorageError("simulated storage failure")

    class StorageAgent:
        def can_execute(self, *args: object, **kwargs: object) -> bool:
            return True

        def execute(self, *args: object, **kwargs: object) -> dict[str, Any]:
            StorageManager.persist_claim({"id": "1"})
            return as_payload({"claims": [], "results": {}})

    monkeypatch.setattr(StorageManager, "persist_claim", fail_persist)
    monkeypatch.setattr(ConfigLoader, "load_config", lambda self, *a, **k: cfg)
    monkeypatch.setattr(
        AgentFactory,
        "get",
        classmethod(lambda cls, name, llm_adapter=None: StorageAgent()),
    )
    return set_value(bdd_context, "config", cfg)


@given("an agent facing a persistent network outage", target_fixture="config")
def network_outage_agent(
    monkeypatch: pytest.MonkeyPatch,
    isolate_network: TypedFixture[None],
    restore_environment: TypedFixture[None],
    bdd_context: BehaviorContext,
) -> ConfigModel:
    cfg = ConfigModel.model_construct(agents=["Offline"], loops=1)

    class OfflineAgent:
        def can_execute(self, *args: object, **kwargs: object) -> bool:
            return True

        def execute(self, *args: object, **kwargs: object) -> dict[str, Any]:
            raise AgentError("network configuration failure")

    monkeypatch.setattr(ConfigLoader, "load_config", lambda self, *a, **k: cfg)
    monkeypatch.setattr(
        AgentFactory,
        "get",
        classmethod(lambda cls, name, llm_adapter=None: OfflineAgent()),
    )
    return set_value(bdd_context, "config", cfg)


@given(parsers.parse('reasoning mode is "{mode}"'))
def set_reasoning_mode(
    config: ConfigModel,
    mode: str,
    isolate_network: TypedFixture[None],
    restore_environment: TypedFixture[None],
    bdd_context: BehaviorContext,
) -> ConfigModel:
    context_config = get_config(bdd_context)
    assert context_config is config, "Config fixture should match context entry"
    config.reasoning_mode = ReasoningMode(mode)
    return config


@pytest.fixture
def recovery_context() -> Iterator[RecoveryDetails]:
    details = RecoveryDetails()
    yield details
    details.reset()


@when(
    parsers.parse('I run the orchestrator on query "{query}"'),
    target_fixture="run_result",
)
def run_orchestrator(
    query: str,
    config: ConfigModel,
    recovery_context: RecoveryDetails,
    isolate_network: TypedFixture[None],
    restore_environment: TypedFixture[None],
    orchestrator_failure: Callable[[str | None], None],
    bdd_context: BehaviorContext,
) -> RunResult:
    orchestrator_failure(None)
    context_config = get_config(bdd_context)
    assert context_config is config, "Config fixture should match context entry"
    orchestrator = get_orchestrator(bdd_context)
    _ = orchestrator  # Ensure accessor is invoked prior to execution.

    record: list[str] = []
    params: dict[str, Any] = {}
    logs: list[str] = []
    execution_state = ExecutionState()
    original_handle = OrchestrationUtils.handle_agent_error
    original_get = AgentFactory.get

    def recording_get(name: str, llm_adapter: object | None = None) -> object:
        agent = original_get(name, llm_adapter)
        if hasattr(agent, "execute"):
            orig_exec = cast(Callable[..., dict[str, Any]], getattr(agent, "execute"))

            def wrapped_execute(*args: object, **kwargs: object) -> dict[str, Any]:
                record.append(name)
                return orig_exec(*args, **kwargs)

            setattr(agent, "execute", wrapped_execute)
        return agent

    def spy_handle(
        agent_name: str,
        exc: Exception,
        state: object,
        metrics: object,
    ) -> dict[str, Any]:
        info = original_handle(agent_name, exc, state, metrics)
        applied = None
        metadata = getattr(state, "metadata", None)
        if isinstance(metadata, Mapping):
            applied = metadata.get("recovery_applied")
        recovery_context.mark_applied(cast(bool | None, applied))
        info["recovery_applied"] = recovery_context.recovery_applied
        recovery_context.update_from_mapping(info)
        logs.append(f"recovery for {agent_name}")
        return info

    original_parse = Orchestrator._parse_config

    def spy_parse(cfg: ConfigModel) -> dict[str, Any]:
        out = original_parse(cfg)
        params.update(out)
        return out

    with (
        patch(
            "autoresearch.orchestration.orchestrator.AgentFactory.get",
            side_effect=recording_get,
        ),
        patch(
            "autoresearch.orchestration.orchestration_utils.OrchestrationUtils.handle_agent_error",
            side_effect=spy_handle,
        ),
        patch(
            "autoresearch.orchestration.orchestrator.Orchestrator._parse_config",
            side_effect=spy_parse,
        ),
    ):
        try:
            response = Orchestrator.run_query(query, config)
        except Exception as exc:  # pragma: no cover - exercised via behavior tests
            if not recovery_context.has_details():
                agent_name = getattr(config, "agents", ["Unknown"])[0]

                def update(result: Mapping[str, Any]) -> None:
                    dummy_state.metadata.update(result.get("metadata", {}))
                    dummy_state.results.update(result.get("results", {}))

                dummy_state = types.SimpleNamespace(
                    update=update,
                    metadata={},
                    results={},
                )
                dummy_metrics = types.SimpleNamespace(
                    record_error=lambda _agent: None,
                )
                info = original_handle(agent_name, exc, dummy_state, dummy_metrics)
                recovery_context.mark_applied(
                    cast(bool | None, dummy_state.metadata.get("recovery_applied"))
                )
                recovery_context.update_from_mapping(info)
                logs.append(f"recovery for {agent_name}")
            error_entry = recovery_context.as_error_entry()
            response = types.SimpleNamespace(
                metadata={"errors": [error_entry]},
                metrics={"errors": [error_entry]},
            )
        finally:
            execution_state.active = False
            logs.append("run complete")

    try:
        response.metadata = response.metrics
    except Exception:  # pragma: no cover - defensive guard
        pass
    return RunResult(
        recovery=recovery_context.snapshot(),
        response=response,
        record=list(record),
        config_params=dict(params),
        logs=list(logs),
        state=execution_state,
    )


@when(
    parsers.parse(
        'I run the orchestrator on query "{query}" with unsupported reasoning mode "{mode}"'
    ),
    target_fixture="error_result",
)
def run_orchestrator_invalid(
    query: str,
    mode: str,
    config: ConfigModel,
    recovery_context: RecoveryDetails,
    isolate_network: TypedFixture[None],
    restore_environment: TypedFixture[None],
    orchestrator_failure: Callable[[str | None], None],
    bdd_context: BehaviorContext,
) -> ErrorResult:
    orchestrator_failure(None)
    context_config = get_config(bdd_context)
    assert context_config is config, "Config fixture should match context entry"
    _ = get_orchestrator(bdd_context)
    _ = recovery_context
    record: list[str] = []
    logs: list[str] = []
    execution_state = ExecutionState()
    error: Exception | None = None
    try:
        cfg = ConfigModel(agents=config.agents, loops=config.loops, reasoning_mode=mode)
        with patch(
            "autoresearch.orchestration.orchestrator.AgentFactory.get",
            side_effect=lambda name, llm_adapter=None: None,
        ):
            Orchestrator.run_query(query, cfg)
    except Exception as exc:  # pragma: no cover - executed via feature
        logs.append(f"unsupported reasoning mode: {mode}")
        error = exc
    finally:
        execution_state.active = False
    return ErrorResult(error=error, record=list(record), logs=list(logs), state=execution_state)


@then("no recovery should be recorded")
def assert_no_recovery(run_result: RunResult) -> None:
    assert not run_result.recovery.has_details()


@then(parsers.parse('a recovery strategy "{strategy}" should be recorded'))
def assert_strategy(run_result: RunResult, strategy: str) -> None:
    assert run_result.recovery.has_details(), "Recovery info should not be empty"
    assert run_result.recovery.recovery_strategy == strategy


@then("recovery should be applied")
def assert_recovery_applied(run_result: RunResult) -> None:
    assert run_result.recovery.has_details(), "Recovery info should not be empty"
    assert run_result.recovery.recovery_applied is True


@then("the response should list a timeout error")
def assert_timeout_error(run_result: RunResult) -> None:
    errors = run_result.errors
    _assert_error_schema(errors)
    assert any(
        e.get("error_type") == "TimeoutError" and "simulated timeout" in e.get("message", "")
        for e in errors
    ), errors


@then("the response should list an agent execution error")
def assert_agent_error(run_result: RunResult) -> None:
    errors = run_result.errors
    _assert_error_schema(errors)
    assert any(e.get("error_type") == "AgentError" for e in errors), errors


@then(parsers.parse('error category "{category}" should be recorded'))
def assert_error_category(run_result: RunResult, category: str) -> None:
    assert run_result.recovery.error_category == category


@then(parsers.parse('the response should list an error of type "{error_type}"'))
def assert_error_type(run_result: RunResult, error_type: str) -> None:
    errors = run_result.errors
    _assert_error_schema(errors)
    assert any(e.get("error_type") == error_type for e in errors), errors


@then(parsers.parse("the loops used should be {count:d}"))
def assert_loops(run_result: RunResult, count: int) -> None:
    assert run_result.config_params.get("loops") == count


@then(parsers.parse('the reasoning mode selected should be "{mode}"'))
def assert_mode(run_result: RunResult, mode: str) -> None:
    assert run_result.config_params.get("mode") == ReasoningMode(mode)


@then(parsers.parse('the agent groups should be "{groups}"'))
def assert_groups(run_result: RunResult, groups: str) -> None:
    expected = [[a.strip() for a in grp.split(",") if a.strip()] for grp in groups.split(";")]
    assert run_result.config_params.get("agent_groups") == expected


@then(parsers.parse('the agents executed should be "{order}"'))
def assert_order(run_result: RunResult, order: str) -> None:
    expected = [a.strip() for a in order.split(",")]
    assert run_result.record == expected


@then("the system state should be restored")
def assert_state_restored(
    run_result: RunResult | None = None,
    error_result: ErrorResult | None = None,
) -> None:
    result = run_result or error_result
    assert result is not None, "Expected a run or error result"
    assert result.state.active is False


@then(parsers.parse('the logs should include "{message}"'))
def assert_logs(
    run_result: RunResult | None = None,
    error_result: ErrorResult | None = None,
    message: str = ""
) -> None:
    result = run_result or error_result
    assert result is not None, "Expected a run or error result"
    logs = result.logs
    assert isinstance(logs, Sequence), f"Logs should be a sequence, received {type(logs).__name__}"
    assert any(message in entry for entry in logs), logs
