# UX Measurement Plan

This plan operationalizes the acceptance criteria in the
[UX Improvements Specification](ux-improvements-spec.md). It defines telemetry
and research methods that span the PySide6 migration phases and keeps parity
with the legacy Streamlit baseline while surfacing progress toward the desktop
experience goals.

## Instrumentation Overview

- **Event routing**: Desktop telemetry publishes through a shared
  `QLoggingCategory` named ``desktop.query`` (exported as
  ``DESKTOP_TELEMETRY_CATEGORY``) and forwards payloads to
  `analytics.dispatch_event`. When analytics is unavailable the helper silently
  degrades to logging only.
- **Component hooks**: Query lifecycle instrumentation now emits:
  - `ui.query.submitted` from `QueryPanel.on_run_clicked` with
    `session_id`, `query_length`, `reasoning_mode`, and `loops`.
  - `ui.query.completed` from `AutoresearchMainWindow.display_results` with the
    shared fields plus `duration_ms` and `result_has_metrics`.
  - `ui.query.failed` from `AutoresearchMainWindow.display_error` with
    `duration_ms`, `error_type`, and `error_message`.
  - `ui.query.cancelled` from the cancellation handler with
    `duration_ms` alongside the shared fields.
- **CLI guard hooks**: The `autoresearch gui` command emits
  `ui.legacy_gui.blocked` when the opt-in flag is absent and
  `ui.legacy_gui.launch` with `port` and `browser` payloads when the legacy UI
  launches. Both rely on the shared analytics dispatcher and fail open when the
  module is unavailable.
- **Component hooks (future)**: Dock toggles and wizard instrumentation remain
  targeted for later phases as originally specified.
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
