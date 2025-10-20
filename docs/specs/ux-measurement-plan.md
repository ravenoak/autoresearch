# UX Measurement Plan

This plan operationalizes the acceptance criteria in the
[UX Improvements Specification](ux-improvements-spec.md). It defines telemetry
and research methods that span the PySide6 migration phases and keeps parity
with the legacy Streamlit baseline while surfacing progress toward the desktop
experience goals.

## Instrumentation Overview

- **Event routing**: Telemetry funnels through the existing analytics sink used
  by the desktop extra. Signals are emitted via `QLoggingCategory` streams and
  forwarded to `analytics.dispatch_event`.
- **Component hooks**: Key PySide6 widgets emit structured events, including:
  - `QLineEdit` query submissions tagged `ui.query.submitted`.
  - `QDockWidget` toggles tagged `ui.progressive_disclosure` with open/close
    payloads.
  - `QMdiSubWindow` creation tagged `ui.window.spawned` with session identifiers.
  - `QWizard` onboarding steps tagged `ui.migration_nudge.step_completed`.
- **Test observability**: CI captures Qt log categories and telemetry payloads
  alongside `pytest` artifacts to validate entry/exit conditions.

## Metric Cadence

- **Query submission latency**
  - Target: P95 ≤ 1.2 seconds.
  - Collection: Telemetry timer from `QLineEdit` submit to `QTableView` render.
  - Phases: P1–P3.
- **Keyboard navigation parity**
  - Target: 100% focusable controls.
  - Collection: `pytest-qt` sweeps and assistive technology spot checks.
  - Phases: P1–P4.
- **Progressive disclosure adoption**
  - Target: ≥ 60% of sessions toggle detail panes.
  - Collection: `QDockWidget` toggle events.
  - Phases: P2.
- **Multi-window sync success**
  - Target: ≥ 90% of sessions avoid error dialogs.
  - Collection: `ui.window.spawned` correlation logs.
  - Phases: P3.
- **Test matrix stability**
  - Target: 100% green CI runs.
  - Collection: `task verify` dashboards and `QtTest` logs.
  - Phases: P4.
- **Migration completion**
  - Target: ≥ 95% PySide6-only launches.
  - Collection: Wizard completion vs. Streamlit fallback events.
  - Phases: P5.
- **User satisfaction**
  - Target: ≥ 4/5 survey rating.
  - Collection: Quarterly persona-aligned survey.
  - Phases: Cross-phase.

## Research and Benchmark Cadence

- **Usability benchmarks**: Conduct moderated sessions at the end of each phase
  using the personas listed in the specification. Capture task completion time,
  error counts, and qualitative friction notes.
- **Telemetry reviews**: Weekly dashboards summarize event volumes, latency, and
  anomaly detections. Findings feed into the parity checklist in the migration
  guide.
- **Accessibility audits**: Perform full WCAG regression tests during P2, P3,
  and P4 using screen readers (NVDA, VoiceOver) and high-contrast modes. Archive
  reports with release artifacts.
- **Regression gates**: Configure CI to fail when telemetry coverage drops below
  thresholds (e.g., missing `ui.query.submitted` events) by asserting presence in
  log captures.

## Data Stewardship

- Store telemetry in anonymized form with session-scoped identifiers only.
- Rotate logs every 30 days and redact sensitive query inputs before export.
- Document metric definitions and dashboards in the shared analytics workspace
  referenced in the migration guide.
