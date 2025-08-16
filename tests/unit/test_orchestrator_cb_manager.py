from autoresearch.config.models import ConfigModel


def test_circuit_breaker_state_is_instance_isolated(monkeypatch, orchestrator_runner):
    cfg = ConfigModel(loops=1, agents=["Synthesizer"])

    call = {"count": 0}

    def fail_first(
        agent_name,
        state,
        config,
        metrics,
        callbacks,
        agent_factory,
        storage_manager,
        loop,
        cb_manager,
    ):
        call["count"] += 1
        if call["count"] == 1:
            cb_manager.update_circuit_breaker(agent_name, "critical")
        return 0

    monkeypatch.setattr(
        "autoresearch.orchestration.execution._execute_agent",
        fail_first,
    )

    o1 = orchestrator_runner()
    o2 = orchestrator_runner()

    o1.run_query("q", cfg)
    o2.run_query("q", cfg)

    state1 = o1.get_circuit_breaker_state("Synthesizer")
    state2 = o2.get_circuit_breaker_state("Synthesizer")

    assert state1["failure_count"] > 0
    assert state2["failure_count"] == 0
    assert state2["state"] == "closed"
