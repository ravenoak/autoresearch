@behavior @error_recovery
Feature: Basic error recovery
  Scenario: record a recovery strategy
    Given a failing operation
    When recovery is attempted
    Then a recovery strategy "retry_with_backoff" should be recorded
