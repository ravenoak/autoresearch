# UX Measurement Plan

This plan operationalizes the acceptance criteria in the
[UX Improvements Specification](ux-improvements-spec.md). It defines telemetry
and research methods that span the PySide6 migration phases and keeps parity
with the legacy Streamlit baseline while surfacing progress toward the desktop
experience goals.

## Overview

This measurement plan defines UX metrics and telemetry for the desktop interface migration. It covers user interaction patterns, performance metrics, and accessibility compliance tracking.

## Algorithms

The measurement system uses event-driven telemetry with structured logging. Key algorithms include:
- Event deduplication using session-based grouping
- Performance metric aggregation with rolling averages
- User journey mapping based on interaction sequences

## Invariants

- All user interactions are logged with session context
- Telemetry data is anonymized before storage
- Measurement overhead must not exceed 5% of UI response time
- Accessibility metrics are collected for all interactive elements

## Proof Sketch

The measurement system maintains data integrity through:
1. Structured event validation at collection time
2. Deduplication logic prevents double-counting
3. Performance impact monitoring ensures minimal overhead
4. Accessibility compliance tracking validates inclusive design

## Simulation Expectations

The measurement system should handle:
- High-frequency interaction scenarios (100+ events/second)
- Network interruption scenarios (offline telemetry buffering)
- Multi-session user workflows (cross-session journey tracking)
- Accessibility testing scenarios (screen reader compatibility)

## Traceability

- **Event Schema**: Defined in `src/autoresearch/ui/telemetry.py`
- **Analytics Pipeline**: Implemented in `src/autoresearch/analytics/`
- **Compliance Tracking**: Integrated with accessibility test suite
- **Performance Monitoring**: Dashboard available at `/ui/metrics`

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
- **Terminal experience hooks**: The Textual dashboard emits
  `cli.tui.launch`, `cli.tui.exit`, and `cli.tui.fallback` events with
  `tty_detected`, `bare_mode`, and `session_duration_ms`. The prompt wrapper
  emits `cli.prompt.enhanced` when prompt-toolkit is active and
  `cli.prompt.basic` when Typer handles the input. Rich helper invocations log
  `cli.render.rich` or `cli.render.plain` tagged with the calling command.
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
- **Terminal adoption**
  - Target: ≥ 60% of TTY sessions opt into enhanced prompts and ≥ 30% launch
    the Textual dashboard during a workflow.
  - Collection: `cli.prompt.enhanced` and `cli.tui.launch` counters segmented
    by TTY detection.
  - Phases: Cross-phase after CLI enhancements ship.
- **Bare-mode regression guard**
  - Target: 0 Rich render invocations in bare-mode or piped contexts.
  - Collection: `cli.render.rich` vs. `cli.render.plain` telemetry audits.
  - Phases: Continuous monitoring.

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
  thresholds (missing `ui.query.submitted` events) by asserting presence in
  log captures.

## Data Stewardship

- Store telemetry in anonymized form with session-scoped identifiers only.
- Rotate logs every 30 days and redact sensitive query inputs before export.
- Document metric definitions and dashboards in the shared analytics workspace
  referenced in the migration guide.
