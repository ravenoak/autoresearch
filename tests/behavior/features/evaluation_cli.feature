Feature: Evaluation CLI
  Validate the evaluation harness CLI behavior for dry-run execution.

  Scenario: Dry-run evaluation produces telemetry summary and artifacts
    Given the evaluation harness runner is stubbed for telemetry
    When I run `autoresearch evaluate run truthfulqa --dry-run --limit 1`
    Then the CLI should exit successfully
    And the evaluation summary output should list the stubbed telemetry
    And the evaluation artifacts should reference the stubbed paths
