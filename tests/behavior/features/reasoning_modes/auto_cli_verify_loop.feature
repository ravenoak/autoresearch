@behavior @reasoning_modes
Feature: AUTO CLI reasoning captures planner, scout gate, and verification loop
  Background:
    Given loops is set to 2 in configuration
    And reasoning mode is "auto"
    And the planner proposes verification tasks

  Scenario: AUTO mode CLI run escalates after scout gate and records verification badges
    When I run the AUTO reasoning CLI for query "scout gate verification rehearsal"
    Then the CLI scout gate decision should escalate to debate
    And the CLI audit badges should include "supported" and "needs_review"
    And the CLI output should record verification loop metrics
