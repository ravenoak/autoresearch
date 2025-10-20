# Streamlit UI (Maintenance Only)

## Overview

The Streamlit interface is frozen in maintenance-only mode while the project
completes the PySide6 migration. Supported work is limited to preserving the
legacy launch path, configuration switches, and core visualization widgets
already in production. New feature requests, UI changes, and integration work
must target the PySide6 desktop client; see the [Streamlit refactor plan][plan]
for the deprecation schedule and migration milestones.

## Supported Surface Area

- **Launcher glue**: `launch()` and related helpers in
  `src/autoresearch/streamlit_ui.py` remain callable for existing automation.
- **Telemetry toggles**: Opt-in analytics flags continue to respect regulated
  environment requirements.
- **Data preview widgets**: Current summary tables, trace viewers, and status
  panels render without layout or styling changes.

These behaviors are regression-tested only to ensure compatibility with
archived deployments; their scope does not expand.

## Frozen Scope and Responsibilities

- Accept only fixes for security issues, crashes, or regressions affecting the
  supported surface area.
- Permit behavioral changes solely when required for the sunset plan (for
  example, new deprecation warnings or migration affordances).
- Route enhancements, UX revisions, and integration work through the PySide6
  client documented in [docs/specs/pyside-desktop.md][pyside6].

## Traceability

- **Modules (archived legacy coverage)**
  - [src/autoresearch/streamlit_ui.py][module]
- **Tests (archived legacy suite)**
  - [tests/unit/legacy/test_streamlit_ui_helpers.py][tests]
- **Forward development path**
  - Streamlit successors must reference [docs/specs/pyside-desktop.md][pyside6]
    for new work.

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
