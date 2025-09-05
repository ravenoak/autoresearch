# Add proof sketches to core specs

## Context
The spec linter reports missing `Proof Sketch` sections in
`docs/specs/cli-utils.md`, `docs/specs/api.md`, and `docs/specs/config.md`.
The API spec also lacks a top-level heading. These gaps block specification
compliance and cause `task check` to fail.

## Additional specs
The following algorithm documents lack `## Correctness` or `## Complexity`
sections and may need proof sketches:

- docs/algorithms/README.md
- docs/algorithms/__init__.md
- docs/algorithms/__main__.md
- docs/algorithms/a2a_interface.md
- docs/algorithms/api_auth_error_paths.md
- docs/algorithms/api_authentication.md
- docs/algorithms/api_rate_limiting.md
- docs/algorithms/api_streaming.md
- docs/algorithms/cli_backup.md
- docs/algorithms/cli_helpers.md
- docs/algorithms/cli_utils.md
- docs/algorithms/config_hot_reload.md
- docs/algorithms/config_utils.md
- docs/algorithms/data_analysis.md
- docs/algorithms/dialectical_coordination.md
- docs/algorithms/distributed_coordination.md
- docs/algorithms/distributed_perf.md
- docs/algorithms/distributed_workflows.md
- docs/algorithms/error_recovery.md
- docs/algorithms/error_utils.md
- docs/algorithms/errors.md
- docs/algorithms/extensions.md
- docs/algorithms/interfaces.md
- docs/algorithms/kg_reasoning.md
- docs/algorithms/llm_adapter.md
- docs/algorithms/logging_utils.md
- docs/algorithms/mcp_interface.md
- docs/algorithms/models.md
- docs/algorithms/monitor_cli.md
- docs/algorithms/orchestration.md
- docs/algorithms/output_format.md
- docs/algorithms/ranking_formula.md
- docs/algorithms/resource_monitor.md
- docs/algorithms/search.md
- docs/algorithms/search_ranking.md
- docs/algorithms/semantic_similarity.md
- docs/algorithms/source_credibility.md
- docs/algorithms/storage.md
- docs/algorithms/storage_backends.md
- docs/algorithms/storage_backup.md
- docs/algorithms/storage_eviction.md
- docs/algorithms/streamlit_app.md
- docs/algorithms/streamlit_ui.md
- docs/algorithms/synthesis.md
- docs/algorithms/test_tools.md
- docs/algorithms/token_budgeting.md
- docs/algorithms/tracing.md
- docs/algorithms/validation.md
- docs/algorithms/visualization.md
- docs/algorithms/weight_tuning.md

## Dependencies
None.

## Acceptance Criteria
- Each spec includes a top-level `#` heading and a `## Proof Sketch` section.
- `uv run python scripts/lint_specs.py` passes without missing heading errors.
- `task check` no longer fails due to spec linter warnings.

## Status
Open
