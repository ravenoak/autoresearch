# Behavior Tests

This directory contains the pytest-bdd scenarios for Autoresearch. Some tests
require optional features that are not installed during a normal development
setup.

## Installing extras

Behavior tests rely on optional features such as the Streamlit UI and the DuckDB
VSS extension. Install all extras to ensure every scenario can run:

```bash
poetry install --with dev --all-extras
```

## Running extra tests

Use pytest markers to execute these scenarios separately if you do not want to
run the entire suite:

```bash
# Scenarios that need the UI extra
poetry run pytest tests/behavior -m requires_ui

# Scenarios that need the VSS extra
poetry run pytest tests/behavior -m requires_vss
```

Scenarios with these markers are skipped when the corresponding extras are not
installed. After installing all extras you may simply run `pytest tests/behavior`
to execute every scenario.

