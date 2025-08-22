Feature: Monitor CLI
  As a user
  I want to inspect system metrics
  So that I can monitor resource usage

  Background:
    Given the application is running

  Scenario: Basic metric display
    When I run `autoresearch monitor`
    Then the monitor command should exit successfully
    And the monitor output should show CPU and memory usage

  Scenario: Watch mode displays metrics continuously
    When I run `autoresearch monitor -w`
    Then the monitor command should exit successfully
    And the monitor output should show CPU and memory usage
    And the monitor should refresh every second

  Scenario: Metrics backend unavailable
    When I run `autoresearch monitor` with metrics backend unavailable
    Then the monitor command should exit with an error
    And the monitor output should include a friendly metrics backend error message

  Scenario: Resource monitoring for a duration
    When I run `autoresearch monitor resources -d 1`
    Then the monitor command should exit successfully
    And the monitor output should show CPU and memory usage

