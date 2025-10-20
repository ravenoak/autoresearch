# UI Testing Procedures

This guide summarizes how we test Autoresearch user interfaces and how to run
key workflows. It covers active PySide6 desktop flows, CLI coverage, and
behavior-driven checks. Streamlit guidance is retained as a legacy appendix.

## Testing Framework Overview

Autoresearch layers several styles of UI validation:

1. **Desktop smoke tests** ensure PySide6 widgets render and respond safely.
2. **Desktop integration tests** drive the full window and orchestration flow.
3. **CLI checks** exercise Typer commands with mocked orchestration hooks.
4. **Behavior-driven scenarios** describe user stories in Gherkin for shared
   flows across surfaces.

## Preparing the Test Environment

- Use Python 3.12+ and install extras through `uv`.
- Create a virtual environment and install editable dependencies:

  ```bash
  uv venv
  uv pip install -e '.[full,parsers,git,llm,dev]'
  ```

- For the leanest setup run:

  ```bash
  uv venv
  uv pip install -e '.[test,ui]'
  ```

- Always invoke pytest through `uv run --extra test` so the correct extras are
  loaded.

## PySide6 Desktop Testing

Desktop UI coverage lives under `tests/ui/desktop/` and relies on PySide6,
pytest-qt, and optional Qt WebEngine bindings.

### Dependencies, markers, and skips

- Every module begins with `pytest.importorskip` so the suite is skipped cleanly
  when PySide6 or Qt WebEngine is unavailable.
- Tests are tagged with `@pytest.mark.requires_ui`; combine this marker with the
  `[ui]` extra when running locally or in CI.
- Integration fixtures set `AUTORESEARCH_SUPPRESS_DIALOGS=1` to disable modal
  prompts. Export the same variable yourself when invoking tests directly.
- PySide6 runs best headless when `QT_QPA_PLATFORM=offscreen` is available; set
  it if your environment lacks a display server.

### Working with pytest-qt

- The `qtbot` fixture drives widgets. Add widgets with `qtbot.addWidget(widget)`
  so pytest-qt tracks clean-up and event processing.
- Use helpers such as `qtbot.wait`, `qtbot.waitUntil`, and `qtbot.mouseClick`
  to advance the event loop and simulate user interaction.
- Prefer object lookups via `findChild` or exported properties on widgets so
  tests remain resilient to layout changes.

### Smoke-test pattern

Smoke coverage focuses on individual widgets. The example below, adapted from
`test_component_smoke.py`, highlights the structure:

```python
QtWidgets = pytest.importorskip("PySide6.QtWidgets", exc_type=ImportError)
QPushButton = QtWidgets.QPushButton

pytestmark = pytest.mark.requires_ui


def test_metrics_dashboard_smoke(qtbot):
    dashboard = MetricsDashboard()
    qtbot.addWidget(dashboard)

    dashboard.update_metrics({"system": {"cpu_percent": 37.5}})
    toggle = dashboard.findChild(QPushButton, "metrics-dashboard-toggle")
    if toggle.isEnabled():
        qtbot.mouseClick(toggle, Qt.LeftButton)
    dashboard.clear()
```

Key points:

- Guard imports so the test self-skips when dependencies are missing.
- Reuse widget IDs (`metrics-dashboard-toggle`) for stable lookups.
- Branch on widget state instead of assuming optional controls are enabled.

### Integration-test pattern

Integration coverage drives the full main window and patches long-running
threads. `tests/ui/desktop/test_desktop_integration.py` demonstrates the core
shape:

```python
class _ImmediateThreadPool:
    def start(self, worker):
        worker.run()

@pytest.fixture(autouse=True)
def _patch_globals(monkeypatch):
    monkeypatch.setenv("AUTORESEARCH_SUPPRESS_DIALOGS", "1")
    monkeypatch.setattr(QtCore.QThreadPool, "globalInstance",
                        staticmethod(lambda: _ImmediateThreadPool()))


def test_main_window_runs_query(qtbot, monkeypatch):
    class DummyOrchestrator:
        def run_query(self, query, config):
            return QueryResponse(query=query, answer="Structured response")

    monkeypatch.setattr(main_window_module, "Orchestrator", DummyOrchestrator)

    window = main_window_module.AutoresearchMainWindow()
    qtbot.addWidget(window)

    window.query_panel.set_query_text("How do dialectical agents coordinate?")
    qtbot.mouseClick(window.query_panel.run_button, Qt.LeftButton)
    qtbot.waitUntil(lambda: window.results_display.current_result is not None)
```

Integration best practices:

- Replace thread pools and timers with synchronous stand-ins to keep tests
  deterministic.
- Patch orchestrator and formatter dependencies to avoid network access and
  heavy renderers.
- Wait for `results_display.current_result` or other explicit signals before
  asserting state.

### Running the desktop suites

- Run only desktop tests:

  ```bash
  uv run --extra test --extra ui pytest tests/ui/desktop -m "requires_ui"
  ```

- Focus on a single widget or keyword:

  ```bash
  uv run --extra test --extra ui pytest -k "query_panel" tests/ui/desktop
  ```

Set `AUTORESEARCH_SUPPRESS_DIALOGS=1` (and optionally `QT_QPA_PLATFORM`), then
launch pytest through `uv run` so Qt bindings resolve correctly.

## CLI Component Testing

CLI components rely on Typer and are exercised with `typer.testing.CliRunner`.
Mock the orchestration layer to return deterministic `QueryResponse` payloads,
then assert on exit codes and printed output.

```python
from typer.testing import CliRunner
from autoresearch.main import app


def test_query_command(monkeypatch):
    runner = CliRunner()
    result = runner.invoke(app, ["query", "What is the capital of France?"])
    assert result.exit_code == 0
    assert "Paris" in result.stdout
```

## Behavior-Driven Development (BDD)

Behavior suites live beside the unit tests and use `pytest-bdd`. Write user
stories in Gherkin, back them with fixtures such as `bdd_context`, and reuse
shared steps so features remain concise.

## Appendix A: Streamlit (Legacy)

Streamlit UI coverage is deprecated and retained only for archival reference.
New work should target the PySide6 desktop shell. When maintaining historical
checks:

- Mock Streamlit modules to avoid launching a live server.
- Limit assertions to verifying that callbacks render markdown or trigger the
  expected orchestration hooks.
- Tag any remaining Streamlit tests with `requires_ui` and annotate them as
  legacy so they can be removed once the desktop client fully replaces the web
  prototype.
