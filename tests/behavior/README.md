# Behavior Tests

This directory contains the pytest-bdd scenarios for Autoresearch. Some tests
require optional features that are not installed during a normal development
setup.

## Installing extras

Behavior tests rely on optional features such as the Streamlit UI and the DuckDB
VSS extension. Install all extras with **uv** before running the scenarios:

```bash
uv pip install -e '.[full,dev]'
```

## Running extra tests

Use pytest markers to execute these scenarios separately if you do not want to
run the entire suite. `requires_ui` scenarios need the `ui` extra while
`requires_vss` scenarios depend on the `vss` extra:

```bash
# Scenarios that need the UI extra
uv run pytest tests/behavior -m requires_ui

# Scenarios that need the VSS extra
uv run pytest tests/behavior -m requires_vss
```

Scenarios with these markers are skipped when the corresponding extras are not
installed. After installing all extras you may simply run `uv run pytest tests/behavior`
to execute every scenario.

## Helper fixtures

The steps reuse fixtures in `steps/common_steps.py` to maintain isolation
between scenarios. The `reset_global_registries` fixture clears agent and
storage registries and prepares a temporary DuckDB database for each test.

For interface tests that need deterministic orchestrator output, the
`dummy_query_response` fixture patches `Orchestrator.run_query` to return a
predefined `QueryResponse` including metrics and the sequence of agents
invoked. This enables precise assertions about payload contents and agent
ordering without sharing state across scenarios.


## Running CLI and recovery scenarios

Run the CLI and error-recovery features individually when developing:

```bash
uv run pytest tests/behavior/features/config_cli.feature::Update_reasoning_configuration
uv run pytest tests/behavior/features/reasoning_mode_cli.feature
uv run pytest tests/behavior/features/error_recovery.feature
```

## New features

- `api_config.feature` exercises the configuration endpoints exposed by the
  HTTP API.
- `visualize_metrics_cli.feature` documents the planned
  `visualize-metrics` CLI command until implementation lands.
