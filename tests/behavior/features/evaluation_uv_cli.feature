Feature: Evaluation CLI via uv
  Validate the evaluation harness when invoked through uv run wrappers.

  Scenario: Dry-run evaluation via uv run surfaces metrics and artifacts
    Given the evaluation harness runner is stubbed for telemetry
    When I run `uv run autoresearch evaluate run truthfulqa --dry-run --limit 1`
    Then the CLI should exit successfully
    And the evaluation summary output should list the stubbed telemetry
    And the evaluation summary table should include the metric columns
    And the evaluation artifacts should reference the stubbed paths
