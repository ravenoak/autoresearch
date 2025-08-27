@behavior @reasoning_modes
Feature: Parallel group merging
  Scenario: Each group contributes one claim
    Given two agent groups
    When the orchestrator runs them in parallel
    Then the reasoning should contain two claims
    And each claim should come from a distinct group
