# UX Improvements Specification

## Overview

This specification aligns the Autoresearch UX roadmap with the milestones in
the [PySide6 Migration and Streamlit Removal Plan][pyside6-plan].
Each phase reuses the migration plan's structure while reframing the goals
around user experience outcomes for the desktop interface. The document
prioritizes dialectical analysis (evaluating trade-offs between PySide6 and
Streamlit) and Socratic inquiry (posing guiding questions for each phase) to
steer the team toward sustainable improvements.

## Guiding Principles

- **Progressive disclosure**: Reveal complexity gradually while preserving
  expert depth for advanced users.
- **Accessibility parity**: Maintain WCAG 2.1 AA compliance established in the
  Streamlit interface and extend it through Qt-native affordances.
- **Multi-window fluency**: Provide synchronized workspaces that respect
  desktop conventions and the needs of power users.
- **Traceable validation**: Ensure that every UX story maps to PySide6
  components and automated tests.

## Personas Aligned to Migration Phases

- **Rapid Explorer (Phase 1 focus)**: Researchers who need a lightweight
  desktop entry point mirroring the existing Streamlit workflows.
- **Configuration Curator (Phase 2 focus)**: Operators managing complex
  pipelines who require parity with Streamlit features and confidence in
  accessibility support.
- **Insights Strategist (Phase 3 focus)**: Power users comparing multiple
  investigations, expecting multi-window orchestration and advanced
  visualizations.
- **Quality Steward (Phase 4 focus)**: QA and release engineers verifying
  cross-platform, accessibility, and performance requirements.
- **Change Champion (Phase 5 focus)**: Documentation authors and customer
  success leads guiding users through the transition away from Streamlit.

## Phased UX Roadmap

### Phase 1: PySide6 POC Implementation (2 weeks)

- **Guiding question**: Does the native desktop entry point preserve the
  essential UX affordances from Streamlit's MVP?
- **Primary personas**: Rapid Explorer, Configuration Curator (baseline)
- **Key UX stories**:
  - As a Rapid Explorer, I can enter a query, submit it, and review results in
    a single window without regressions from Streamlit.
  - As a Configuration Curator, I can adjust core runtime parameters using
    accessible controls with keyboard navigation.
- **Shared reference**: Use the
  [Phase 1 wireframes](../diagrams/pyside6_layout.md#visual-references) to
  verify layout, feedback, and gating details during story kick-offs.
- **Success metrics**:
  - Functional parity demo covering query submission and results display.
  - Keyboard-only interaction path validated through exploratory testing.
  - Initial accessibility audit documenting color contrast and focus order
    deltas.

### Phase 2: Feature Parity Implementation (6 weeks)

- **Guiding question**: Where does PySide6 offer superior UX leverage compared
  with Streamlit, and how do we ensure accessibility parity while reaching
  feature completeness?
- **Primary personas**: Configuration Curator, Rapid Explorer
- **Key UX stories**:
  - As a Configuration Curator, I can manage presets, edit configuration files,
    and trust that validation feedback mirrors Streamlit's safeguards.
  - As a Rapid Explorer, I can toggle progressive disclosure controls to zoom
    from TL;DR summaries to full trace detail without losing context.
  - As any user, I can rely on WCAG-equivalent assistive technologies (screen
    readers, high-contrast themes, keyboard cues).
- **Success metrics**:
  - Feature-complete parity checklist signed off with accessibility parity
    reports.
  - Progressive disclosure usability test with at least three internal users,
    capturing task completion times and qualitative feedback.
  - Automated accessibility smoke tests executing in CI for the PySide6 UI.

### Phase 3: Professional Features (4 weeks)

- **Guiding question**: How do we expand the UX for power users without
  overwhelming newcomers?
- **Primary personas**: Insights Strategist, Configuration Curator
- **Key UX stories**:
  - As an Insights Strategist, I can open multiple synchronized windows to
    compare queries, with shared session state and consistent keyboard
    shortcuts.
  - As a Configuration Curator, I can annotate knowledge graphs, drag-and-drop
    artifacts, and export professional reports.
- **Success metrics**:
  - Multi-window workflow validated by side-by-side comparison tasks.
  - Latency budget: window orchestration actions respond within 300 ms on
    reference hardware.
  - Accessibility parity maintained through regression testing across new
    interactions (graph annotations, drag-and-drop).

### Phase 4: Testing and Quality Assurance (3 weeks)

- **Guiding question**: Do our automated tests and manual protocols give the
  Quality Steward confidence across platforms?
- **Primary personas**: Quality Steward, Configuration Curator
- **Key UX stories**:
  - As a Quality Steward, I can run cross-platform PySide6 test suites covering
    unit, integration, accessibility, and performance aspects.
  - As a Configuration Curator, I can validate that PySide6 builds maintain UX
    consistency before the Streamlit interface is deprecated.
- **Success metrics**:
  - Full PySide6 test matrix passing in CI (Windows, macOS, Linux).
  - Accessibility parity report generated automatically per release.
  - Performance benchmarks showing equal or better responsiveness than the
    Streamlit baseline.

### Phase 5: Deprecation and Removal (2 weeks)

- **Guiding question**: How do we support Change Champions and end users during
  the transition away from Streamlit while preserving UX trust?
- **Primary personas**: Change Champion, Rapid Explorer
- **Key UX stories**:
  - As a Change Champion, I can reference clear documentation describing the
    PySide6 experience, highlighting multi-window workflows and progressive
    disclosure improvements.
  - As a Rapid Explorer, I can rely on PySide6 defaults and onboarding flows
    that match or surpass the Streamlit experience.
- **Success metrics**:
  - Documentation updates published with before/after UX narratives.
  - Support tickets related to the migration resolved within one release
    cadence.
  - Streamlit code removal completed with no open UX regressions.

## Cross-Phase Success Metrics

- Task completion times for core workflows improve by 15% compared with the
  Streamlit baseline.
- User satisfaction (internal surveys) reaches at least 4/5 for progressive
  disclosure clarity, accessibility confidence, and multi-window utility.
- Automated accessibility and regression test coverage exceeds 80% of critical
  PySide6 components.
- All UX stories have traceable tickets linking to implementation changes and
  validation artifacts.

## Traceability Matrix

| UX Story | Component IDs | Covered Tests | Status |
| --- | --- | --- | --- |
| Query parity (P1) | C1,C2,C3 | B-UI-DESK-001/T-UI-004/T-UI-002 | Covered |
| Progressive disclosure controls | C3, C7 | T-UI-003, T-UI-004 | Covered |
| Accessibility parity | C2, C3, C4 | T-UI-002, T-UI-001 | Partial |
| Knowledge graph annotations | C3, C6 | T-UI-003, T-UI-001 | Partial |
| Drag-and-drop imports | C4, C7 | T-UI-001 | Partial |
| Export pipelines | C3, C7 | — | Backlog |
| Multi-window comparison | C1, C5 | — | Backlog |
| Performance dashboards | C3, C8 | T-UI-001 | Covered |
| Streamlit GUI regression (archival) | C3 | L-UI-LEGACY-001 | Archived |

Entries marked as *Archived* refer to legacy Streamlit coverage gated by the
`@legacy_streamlit` marker.

### Test ID Legend

- **T-UI-001**:
  [`tests/ui/desktop/test_component_smoke.py`][t-ui-001]
- **T-UI-002**:
  [`tests/ui/desktop/test_query_panel.py`][t-ui-002]
- **T-UI-003**:
  [`tests/ui/desktop/test_results_display.py`][t-ui-003]
- **T-UI-004**:
  [`tests/ui/desktop/test_desktop_integration.py`][t-ui-004]
- **B-UI-DESK-001**:
  [`tests/behavior/features/pyside6_desktop.feature`][b-ui-desk-001]
- **L-UI-LEGACY-001**:
  [`tests/behavior/features/streamlit_gui.feature`][l-ui-legacy-001] *(archival)*

### Test Backlog

- **Multi-window orchestration** — planned coverage in
  [`tests/ui/desktop/integration/test_multi_window.py`][t-multi-window] to
  validate synchronized workspaces and shared session state.
- **Accessibility regression sweep** — expand focus-order and assistive
  technology checks in
  [`tests/ui/desktop/accessibility/test_keyboard_navigation.py`][t-a11y] to
  exercise screen reader cues and high-contrast themes.
- **Drag-and-drop import flows** — deepen coverage in
  [`tests/ui/desktop/test_drag_drop.py`][t-drag-drop] for artifact ingest parity
  with Streamlit.
- **Export pipeline end-to-end** — exercise background export tasks in
  [`tests/ui/desktop/integration/test_export_end_to_end.py`][t-export-e2e] to
  confirm report generation and progress feedback.
- **Performance telemetry stress** — benchmark metrics dashboards in
  [`tests/ui/desktop/performance/test_metrics_dashboard_performance.py`][t-perf]
  to guard latency budgets across tabs.

[t-ui-001]: ../../tests/ui/desktop/test_component_smoke.py
[t-ui-002]: ../../tests/ui/desktop/test_query_panel.py
[t-ui-003]: ../../tests/ui/desktop/test_results_display.py
[t-ui-004]: ../../tests/ui/desktop/test_desktop_integration.py
[t-multi-window]: ../../tests/ui/desktop/integration/test_multi_window.py
[t-a11y]: ../../tests/ui/desktop/accessibility/test_keyboard_navigation.py
[t-drag-drop]: ../../tests/ui/desktop/test_drag_drop.py
[t-export-e2e]: ../../tests/ui/desktop/integration/test_export_end_to_end.py
[t-perf]:
  ../../tests/ui/desktop/performance/test_metrics_dashboard_performance.py
[b-ui-desk-001]: ../../tests/behavior/features/pyside6_desktop.feature
[l-ui-legacy-001]: ../../tests/behavior/features/streamlit_gui.feature

### Component ID Legend

- **C1**: `main_window.py`
- **C2**: `query_panel.py`
- **C3**: `results_display.py`
- **C4**: `config_editor.py`
- **C5**: `session_manager.py`
- **C6**: `knowledge_graph_view.py`
- **C7**: `export_manager.py`
- **C8**: `metrics_dashboard.py`

[pyside6-plan]: ../pyside6_migration_plan.md
