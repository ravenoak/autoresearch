# Spec: docs/orchestrator_state_spec.md

import pytest


class OrchestratorStateMachine:
    """Minimal state machine for orchestrator transitions."""

    def __init__(self) -> None:
        self.state = "Idle"

    def start(self) -> None:
        if self.state != "Idle":
            raise RuntimeError("start only allowed from Idle")
        self.state = "Preparing"

    def launch(self) -> None:
        if self.state != "Preparing":
            raise RuntimeError("launch only allowed from Preparing")
        self.state = "Running"

    def finish(self) -> None:
        if self.state != "Running":
            raise RuntimeError("finish only allowed from Running")
        self.state = "Complete"

    def fail(self) -> None:
        if self.state != "Running":
            raise RuntimeError("fail only allowed from Running")
        self.state = "Error"


def test_start_transition() -> None:
    sm = OrchestratorStateMachine()
    sm.start()
    assert sm.state == "Preparing"
    with pytest.raises(RuntimeError):
        sm.start()


def test_launch_transition() -> None:
    sm = OrchestratorStateMachine()
    sm.start()
    sm.launch()
    assert sm.state == "Running"
    with pytest.raises(RuntimeError):
        sm.launch()


def test_finish_transition() -> None:
    sm = OrchestratorStateMachine()
    sm.start()
    sm.launch()
    sm.finish()
    assert sm.state == "Complete"
    with pytest.raises(RuntimeError):
        sm.finish()


def test_fail_transition() -> None:
    sm = OrchestratorStateMachine()
    sm.start()
    sm.launch()
    sm.fail()
    assert sm.state == "Error"
    with pytest.raises(RuntimeError):
        sm.fail()
