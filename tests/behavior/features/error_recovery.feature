@behavior
Feature: Error Recovery
  As a user
  I want the system to apply recovery strategies
  So transient errors do not halt execution

  Scenario: Error recovery in dialectical reasoning mode
    Given an agent that raises a transient error
    And reasoning mode is "dialectical"
    When I run the orchestrator on query "recover test"
    Then a recovery strategy "retry_with_backoff" should be recorded
    And recovery should be applied

  Scenario: Error recovery in direct reasoning mode
    Given an agent that raises a transient error
    And reasoning mode is "direct"
    When I run the orchestrator on query "recover test"
    Then a recovery strategy "retry_with_backoff" should be recorded
    And recovery should be applied

  Scenario: Error recovery in chain-of-thought reasoning mode
    Given an agent that raises a transient error
    And reasoning mode is "chain-of-thought"
    When I run the orchestrator on query "recover test"
    Then a recovery strategy "retry_with_backoff" should be recorded
    And recovery should be applied
