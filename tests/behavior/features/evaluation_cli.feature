@behavior
Feature: Evaluation CLI dry-run summary
  Validate that the evaluation CLI renders telemetry for dry-run scenarios.

  Background:
    Given the Autoresearch application is running

  Scenario: Render evaluation summary for a dry-run dataset
    Given the evaluation harness is stubbed for dataset "truthfulqa"
    When I run `uv run autoresearch evaluate run truthfulqa --dry-run`
    Then the CLI should exit successfully
    And the evaluation harness should receive a dry-run request for "truthfulqa"
    And the evaluation summary should include metrics for "truthfulqa"
    And the CLI output should list evaluation artifacts for "truthfulqa"
    And the CLI should report the dry-run warning
