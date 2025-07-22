# Behavior Tests

This directory contains the pytest-bdd scenarios for Autoresearch. Some tests
require optional features that are not installed during a normal development
setup.

## Installing extras

To run scenarios that depend on the Streamlit UI or the DuckDB VSS extension,
install the appropriate extras with Poetry:

```bash
poetry install --with dev --extras ui
poetry install --with dev --extras vss
```

## Running extra tests

Use pytest markers to execute these scenarios separately:

```bash
# Scenarios that need the UI extra
poetry run pytest tests/behavior -m requires_ui

# Scenarios that need the VSS extra
poetry run pytest tests/behavior -m requires_vss
```

Scenarios with these markers are skipped when the corresponding extras are not
installed.

