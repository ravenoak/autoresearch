# Textual Dashboard

The Textual dashboard provides a terminal-native view of Autoresearch queries.
It uses the [Textual](https://textual.textualize.io/) framework to render
parallel panels that track cycle progress, reasoning traces, execution metrics,
and knowledge-graph summaries while the orchestrator runs.

- **Usage:** run `autoresearch search --tui "<query>"` when your terminal
  supports TTY interactions. The dashboard mirrors orchestrator callbacks and
  system metrics from `monitor._collect_system_metrics`, so the standard CLI
  output still streams once the session ends.
- **Dependencies:** install the `autoresearch[tui]` extra (or `pip install
  textual`) to enable the dashboard.
- **Fallback behaviour:** if Textual is unavailable, stdout is not a TTY, or
  bare mode is active, the CLI warns and reverts to the legacy plain-text
  renderer. Results are still formatted through `OutputFormatter`.
- **Limitations:** interactive refinements (`--interactive`) and parallel
  agent groups (`--parallel` or `--agent-groups`) currently fall back to the
  legacy renderer. Bare mode (`--bare-mode` or `AUTORESEARCH_BARE_MODE=true`)
  also disables the dashboard to preserve accessibility.

The dashboard terminates cleanly with `q`, restores terminal state, and then
prints the final response using the chosen output format. Use `--verbose` to
inspect additional logs if an error occurs during orchestration.
