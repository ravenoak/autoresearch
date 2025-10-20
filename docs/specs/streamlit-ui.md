# Streamlit UI (Maintenance Only)

## Overview

The Streamlit interface is now in maintenance-only mode while the project
completes the PySide6 migration. Support is limited to preserving the existing
entry points and regression-tested behaviors documented below. New feature
requests, UI experiments, or integrations must route through the PySide6
desktop client initiative; see the [Streamlit support sunset plan][sunset-plan]
for schedule details and migration guidance.

## Supported Surface Area

- **Launcher glue**: `launch()` and related helpers exposed in
  `src/autoresearch/streamlit_ui.py` remain callable to unblock automation
  scripts that hardcode Streamlit entry points.
- **Telemetry toggles**: The opt-in flags and configuration wiring required to
  disable analytics for regulated environments continue to function.
- **Data preview widgets**: Existing summary tables, trace viewers, and status
  panels render with their current layout and styling.

These components are frozen; we do not expand their scope beyond compatibility
and defect corrections.

## Frozen Scope and Responsibilities

- We accept only security patches, crash fixes, and regressions blocking
  supported deployments.
- Behavioral changes must be justified as part of sunset compliance (for
  example, deprecation warnings or migration affordances).
- Any enhancements or UX revisions must target the PySide6 desktop client and
  reference `docs/specs/pyside-desktop.md` instead of this document.

## Traceability

- **Modules (archived legacy coverage)**
  - [src/autoresearch/streamlit_ui.py][m1]
- **Tests (archived legacy suite)**
  - [tests/unit/legacy/test_streamlit_ui_helpers.py][t1]
- **Forward development path**
  - [docs/specs/pyside-desktop.md][pyside6]

## Known Deviation

!!! warning "Security and stability fixes only"
    Streamlit support follows the deprecation timeline in the
    [Streamlit support sunset plan][sunset-plan]. We accept security and
    stability patches exclusively; feature-level work must target the PySide6
    surface area before the final removal milestone.

[sunset-plan]: ./streamlit-refactor-plan.md
[m1]: ../../src/autoresearch/streamlit_ui.py
[t1]: ../../tests/unit/legacy/test_streamlit_ui_helpers.py
[pyside6]: ./pyside-desktop.md
