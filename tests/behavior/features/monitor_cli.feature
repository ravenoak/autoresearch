Feature: Monitor CLI
  As a user
  I want to inspect system metrics and monitor execution
  So that I can understand resource usage and recover from errors

  Background:
    Given the application is running

  Scenario: Display single-run metrics
    When I run `autoresearch monitor`
    Then the monitor command should exit successfully
    And the monitor output should display system metrics

  Scenario: Watch metrics continuously
    When I run `autoresearch monitor -w`
    Then the monitor command should exit successfully
    And the monitor output should display system metrics

  Scenario: Handle invalid flag
    When I run `autoresearch monitor --invalid`
    Then the monitor command should exit with an error
    And the monitor output should include an invalid option message

  Scenario Outline: Monitor run supports <mode> reasoning
    When I start `autoresearch monitor run` in "<mode>" mode and enter "test"
    Then the monitor command should exit successfully

    Examples:
      | mode            |
      | direct          |
      | chain-of-thought|

  Scenario: Recover from orchestrator errors
    When I start `autoresearch monitor run` with a failing query
    Then the monitor command should exit successfully
    And the monitor output should contain an error message
