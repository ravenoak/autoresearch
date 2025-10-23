# Terminal Experience Enhancement Specification

## Overview

This specification codifies the optional Textual dashboard, prompt-toolkit
prompting layer, and Rich layout harmonisation proposed in the UX review. It
extends the CLI surface without regressing accessibility, bare-mode
compatibility, or automated workflows.

## Algorithms

The terminal experience enhancement implements:

- **TTY Detection Algorithm**: Automatic detection of interactive terminals vs. pipes/redirects
- **Layout Optimization**: Dynamic layout adjustment based on terminal dimensions and content complexity
- **Accessibility Layer**: Screen reader compatibility through semantic markup and ARIA-like patterns
- **Performance Balancing**: Frame rate optimization for smooth terminal animations

## Invariants

- **Backward Compatibility**: All existing CLI workflows must continue to function unchanged
- **Accessibility Compliance**: Terminal enhancements must not reduce accessibility
- **Performance Bounds**: Terminal rendering must maintain 60fps minimum
- **Graceful Degradation**: Enhanced features must fall back cleanly when unavailable

## Proof Sketch

The terminal experience maintains reliability through:
1. Comprehensive TTY detection prevents inappropriate enhancement activation
2. Fallback mechanisms ensure basic functionality in all environments
3. Accessibility testing validates screen reader compatibility
4. Performance benchmarking ensures smooth operation

## Simulation Expectations

The terminal system must handle:
- Various terminal emulators (xterm, iTerm2, Windows Terminal, etc.)
- Different terminal sizes and aspect ratios
- Network interruption scenarios (offline operation)
- High-throughput logging scenarios (research monitoring)

## Traceability

- **Textual Dashboard**: `src/autoresearch/ui/tui/dashboard.py`
- **Prompt Enhancement**: `src/autoresearch/main/Prompt.py`
- **Rich Layouts**: `src/autoresearch/cli_utils.py`
- **Accessibility**: `tests/ui/test_terminal_accessibility.py`

## Dialectical framing

- **Thesis:** Invest in Textual, prompt-toolkit, and deeper Rich layouts to make
  monitoring and interactive sessions more legible, navigable, and efficient for
  power users.
- **Antithesis:** Terminal control codes can break scripts, overwhelm screen
  readers, or conflict with bare mode if not isolated.
- **Synthesis:** Deliver an opt-in terminal experience that auto-detects TTY
  contexts, falls back gracefully, and reuses OutputFormatter so automation
  contracts remain intact.

## System context

```
+-----------------+  Typer Commands  +----------------------+  Rich Helpers
| Typer CLI entry | ----------------> | Prompt Abstraction  | ------------+
| points (search, |                   | (prompt-toolkit with |            |
| monitor, tui)   | <---------------- | Typer fallback)      |            |
+-----------------+  Plaintext Path  +----------------------+            |
        |                                                         Launch |
        |                                                         dashboard
        v                                                               |
+------------------+  Hooks/Events  +-----------------------+  Renderables |
| Textual Dashboard| --------------> | Visualization Hooks   | ----------> |
| (panels, charts) | <-------------- | (CLI utils, monitor)  | <----------+
+------------------+  Bare-mode exit +-----------------------+
```

## Components and responsibilities

- **Prompt abstraction:** New `PromptService` module mediates between
  prompt-toolkit and Typer, enabling history, completions, and multi-line entry
  in TTY environments while persisting session history.
- **Textual dashboard:** `TextualDashboardApp` renders orchestration metrics,
  trace panes, and knowledge-graph summaries. It subscribes to
  `VisualizationHooks` and monitor callbacks, and exits cleanly on bare mode or
  non-TTY detection.
- **Rich layout utilities:** Shared helpers render progress, metrics, and
  summaries with Rich components while emitting ASCII fallbacks in bare mode.

## Requirements alignment

- **F-25:** Provide a Textual-powered dashboard that users can opt into when the
  terminal supports TUIs; default flows remain unchanged elsewhere.
- **F-26:** Offer enhanced interactive prompts with history, completions, and
  multi-line editing when prompt-toolkit is present and revert to Typer when it
  is not.
- **F-27:** Consolidate Rich renderables for monitoring and metrics while
  keeping bare-mode/plaintext paths faithful to accessibility guarantees.

## Acceptance criteria

1. Launching `autoresearch tui` (or `search --tui`) on a TTY opens the Textual
   dashboard with panels updating from orchestration and monitor telemetry.
2. Invoking the same command in non-TTY or bare-mode contexts prints a fallback
   message and runs the legacy Typer workflow without control codes.
3. Interactive prompts expose history navigation and completions, persisting per
   session and falling back cleanly when prompt-toolkit is missing.
4. Metrics and summaries use shared Rich helpers by default, while bare mode and
   pipes retain plaintext output identical to current baselines.

## Observability hooks

- Emit `cli.tui.launch`, `cli.tui.exit`, and `cli.tui.fallback` events through
  the analytics dispatcher for dashboard sessions.
- Record prompt-toolkit usage via `cli.prompt.enhanced` and fallback usage via
  `cli.prompt.basic` counters.
- Capture Rich helper usage with structured logs summarising layout type and
  fallback path to support regression analysis.

## Verification strategy

- **Unit tests:** Mock `PromptService` to ensure enhanced prompting is selected
  only when TTY and prompt-toolkit conditions are met.
- **Integration tests:** Exercise the Textual command under TTY and non-TTY
  simulations to confirm fallback behaviour and analytics events.
- **Behavior tests:** Extend BDD coverage for dashboard launch flows, enhanced
  prompts, and bare-mode fallbacks.
- **Documentation:** Update requirements, traceability, and measurement plan to
  reference new instrumentation and success metrics.

## Traceability

- **Modules:** `main/app.py`, `cli_utils.py`, `monitor/`, `ui/tui/`,
  `prompting/prompt_service.py`.
- **Tests:** `tests/behavior/features/terminal_dashboard.feature`,
  `tests/behavior/features/enhanced_prompting.feature`,
  `tests/behavior/features/rich_monitor_layout.feature`, and targeted unit tests
  mocked through `PromptService`.
- **Telemetry:** Metrics in `docs/specs/ux-measurement-plan.md` keep the
  dashboard and prompt experiences observable.
