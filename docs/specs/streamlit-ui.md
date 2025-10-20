# Streamlit UI (Maintenance Only)

## Overview

The Streamlit-driven interface now lives in a maintenance-only track while the
product team completes the PySide6 migration. The only supported effort is to
keep the legacy launch sequence, environment configuration, and baseline
visualization widgets running for existing deployments. Any new feature
requests, UX experiments, or platform integrations must target the PySide6
client instead; the deprecation runway is documented in the [Streamlit refactor
plan][plan].

## Supported Surface Area

- **Launcher glue**: `launch()` and downstream helpers in
  `src/autoresearch/streamlit_ui.py` remain callable for automation that has not
  migrated.
- **Configuration switches**: Existing flag handling, including telemetry opt-in
  logic, must continue to respect regulated environments.
- **Data display widgets**: Legacy summary tables, trace viewers, and status
  panels render exactly as they do today.

Regression coverage is confined to these paths to ensure archived deployments
continue to load; this scope is frozen and does not expand.

## Opt-In Launch Workflow

- The CLI command `autoresearch gui` now checks the
  `AUTORESEARCH_ENABLE_STREAMLIT` environment variable. The legacy Streamlit UI
  only launches when the flag is set to a truthy value such as `1`, `true`,
  `yes`, or `on`.
- When the flag is absent the CLI exits with a migration warning and directs
  operators to the PySide6 desktop app. This keeps the grace-period launch
  constrained to teams who explicitly require the fallback.
- To launch the legacy interface during the maintenance window run:

  ```bash
  AUTORESEARCH_ENABLE_STREAMLIT=1 autoresearch gui --port 8501
  ```

- Encourage teams to move to the PySide6 workflow by default and reserve the
  environment variable opt-in for temporary compatibility.

## Frozen Scope and Responsibilities

- Accept only patches that address security issues, stability risks, or
  regressions within the supported surface area.
- Allow behavioral adjustments solely when required to deliver the sunset plan,
  such as issuing migration warnings or enabling data export for handoff.
- Route enhancements, UX revisions, and integration work through the PySide6
  desktop client described in [docs/specs/pyside-desktop.md][pyside6].

## Traceability

- **Modules (archived legacy coverage)**
  - [src/autoresearch/streamlit_ui.py][module]
- **Tests (archived legacy suite)**
  - [tests/unit/legacy/test_streamlit_ui_helpers.py][tests]
- **Forward development path**
  - New UI investment must go through the PySide6 track in
    [docs/specs/pyside-desktop.md][pyside6]; Streamlit work remains frozen.

## Known Deviation

!!! warning "Security and stability fixes only"
    The Streamlit UI stays in maintenance until its removal milestone in the
    [Streamlit refactor plan][plan]. Only security or stability patches are
    accepted; all feature or UX work must proceed through the PySide6 desktop
    surface area.

[plan]: ./streamlit-refactor-plan.md
[module]: ../../src/autoresearch/streamlit_ui.py
[tests]: ../../tests/unit/legacy/test_streamlit_ui_helpers.py
[pyside6]: ./pyside-desktop.md
