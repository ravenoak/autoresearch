@behavior @reasoning_modes
Feature: AUTO reasoning integrates planner, scout gate, and verification
  Background:
    Given loops is set to 2 in configuration
    And reasoning mode is "auto"
    And the planner proposes verification tasks

  Scenario: AUTO mode escalates after scout gate and records audit badges
    When I run the auto planner cycle for query "audit badge rehearsal"
    Then the scout gate decision should escalate to debate
    And the auto mode audit badges should include "supported" and "needs_review"
    And the planner task graph snapshot should include verification goals
    And the AUTO metrics should record scout samples and agreement
    And the AUTO metrics should include planner depth and routing deltas

  Scenario: AUTO telemetry captures adaptive search strategy improvements
    Given loops is set to 2 in configuration
    And reasoning mode is "auto"
    And the planner proposes verification tasks
    And the scout metadata includes adaptive search strategy signals
    When I run the auto planner cycle for query "adaptive telemetry rehearsal"
    Then the auto planner cycle should surface search strategy telemetry
