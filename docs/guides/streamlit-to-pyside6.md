# Streamlit to PySide6 Migration Guide

## Overview

The PySide6 desktop client replaces the legacy Streamlit interface as the
primary way to run Autoresearch with a native, high-performance workflow.
This guide explains the transition, highlights milestone dates, and gathers
resources so teams can plan their upgrades. Use it alongside the
[PySide6 migration plan](../pyside6_migration_plan.md) for broader program
context and the
[Streamlit support sunset plan](../specs/streamlit-refactor-plan.md) for the
official deprecation timeline.

## Side-by-Side Feature Parity Status

- **Core querying**: PySide6 matches Streamlit features for query authoring,
  result review, metrics, and export flows. Any remaining gaps are tracked in
  the PySide6 parity dashboard referenced in the migration plan.
- **Configuration management**: Desktop builds expose JSON editing, session
  bookmarking, and environment toggles. Streamlit-only toggles now map to
  PySide6 toolbars or dock widgets.
- **Accessibility and theming**: High-contrast themes, keyboard navigation, and
  screen reader annotations ship with PySide6. Streamlit retains only critical
  bug fixes for these surfaces.
- **Extensibility**: Custom widgets and metrics panels move to Qt dockables in
  PySide6. Streamlit component hooks are frozen and will not receive new API
  work.

## Parity Checklist and Dashboard

- Review the [UX Measurement Plan](../specs/ux-measurement-plan.md) for the
  telemetry and research metrics that gate each migration phase.
- Track live progress in the internal parity dashboard shared in release notes;
  it visualizes the acceptance criteria events (e.g., `ui.query.submitted`,
  `ui.window.spawned`) and flags regressions against phase targets.
- Before deprecating a Streamlit workflow, confirm the checklist reports
  "green" for the relevant PySide6 components and that supporting tests exist
  in the paths cited by the UX improvements specification.

## Setup Checklist for the Desktop Extra

1. **Install optional dependencies**
   ```bash
   uv pip install ".[desktop]"
   ```
2. **Initialize the desktop workspace**
   - Run `autoresearch desktop` to generate the PySide6 settings directory and
     confirm the window launches without warnings.
3. **Import legacy sessions (optional)**
   - Export saved Streamlit sessions before uninstalling the `ui` extra.
   - Use the PySide6 session manager to import JSON snapshots.
4. **Update automation**
   - Replace Streamlit launch scripts with the desktop entry point in CI/CD or
     packaging manifests.

## Troubleshooting

- **Missing Qt platform plugins**: Ensure the `desktop` extra installed system
  prerequisites. On Linux, set `QT_QPA_PLATFORM=wayland` or `xcb` depending on
  the compositor.
- **Conflicting extras**: Remove the legacy `ui` extra to avoid dependency
  clashes with PySide6. Run `uv pip uninstall streamlit` if it was manually
  added.
- **Headless servers**: Use the CLI or API flows instead of the desktop app.
  The PySide6 client requires a display server and will not start on pure
  headless environments.
- **Regressions compared with Streamlit**: Log issues with screenshots, parity
  references, and reproduction steps so the migration team can triage them
  during the active support window.

## FAQs for Legacy Users

- **Can we keep Streamlit for a while longer?** Streamlit remains maintenance
  only during the grace period noted in the sunset plan. Security fixes ship,
  but feature requests are redirected to PySide6.
- **What if a Streamlit-only workflow is missing in PySide6?** Check the parity
  dashboard in the migration plan. Report blockers with details so they can be
  prioritized.
- **How do we test the PySide6 UI alongside Streamlit?** Use feature flags or
  separate virtual environments. The `desktop` extra can coexist temporarily,
  but disable Streamlit in production rollouts to minimize confusion.
- **Where can we get migration help?** Attend the weekly office hours announced
  in release notes, or reach out via the support channel listed in the sunset
  plan.
