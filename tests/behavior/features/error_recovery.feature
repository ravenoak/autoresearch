@behavior
Feature: Error Recovery
  As a user
  I want the system to apply recovery strategies
  So transient errors do not halt execution

  Scenario: Transient error triggers recovery
    Given an agent that raises a transient error
    When I run the orchestrator on query "recover test"
    Then a recovery strategy "retry_with_backoff" should be recorded
    And recovery should be applied
