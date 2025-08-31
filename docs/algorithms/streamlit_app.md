# Streamlit App

Experimental web interface for Autoresearch.

## Features
- Config editor, guided tour, and accessibility options.
- Runs queries with `Orchestrator` and displays answers and citations.
- Streams logs and metrics through a custom log handler.

## References
- [`streamlit_app.py`](../../src/autoresearch/streamlit_app.py)
- [../specs/streamlit-app.md](../specs/streamlit-app.md)

## Simulation

Automated tests confirm streamlit app behavior.

- [Spec](../specs/streamlit-app.md)
- [Tests](../../tests/integration/test_streamlit_gui.py)
