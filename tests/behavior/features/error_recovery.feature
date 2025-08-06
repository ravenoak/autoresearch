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

  Scenario: Recovery after storage failure
    Given a storage layer that raises a StorageError
    When I run the orchestrator on query "recover test"
    Then a recovery strategy "fail_gracefully" should be recorded
    And error category "critical" should be recorded
    And recovery should be applied
    And the response should list an error of type "StorageError"

  Scenario: Recovery after persistent network outage
    Given an agent facing a persistent network outage
    When I run the orchestrator on query "recover test"
    Then a recovery strategy "fallback_agent" should be recorded
    And error category "recoverable" should be recorded
    And recovery should be applied
    And the response should list an error of type "AgentError"
