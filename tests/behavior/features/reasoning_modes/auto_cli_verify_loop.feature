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
    And the AUTO metrics should record scout samples and agreement

  Scenario: AUTO mode completes the configured PRDV verification loops
    When I run the AUTO reasoning CLI for query "prdv verification rehearsal"
    Then the CLI scout gate decision should escalate to debate
    And the CLI output should record verification loop metrics
    And the CLI verification loops should match the configured count
    And the AUTO metrics should record scout samples and agreement

  Scenario: AUTO mode CLI run exits directly when the scout gate declines debate
    Given the scout gate will force a direct exit
    When I run the AUTO reasoning CLI for query "scout gate direct exit rehearsal"
    Then the CLI should exit directly without escalation
    And the AUTO metrics should record scout samples and agreement

  Scenario: AUTO direct exit hedges unsupported claims
    Given the scout gate will force a direct exit
    When I run the AUTO reasoning CLI for query "unsupported direct exit rehearsal"
    Then the CLI should exit directly without escalation
    And the CLI TLDR should warn about unsupported claims
    And the CLI key findings should omit unsupported claims

  Scenario: AUTO debate flow hedges unsupported claims
    When I run the AUTO reasoning CLI for query "unsupported debate rehearsal"
    Then the CLI scout gate decision should escalate to debate
    And the CLI TLDR should warn about unsupported claims
    And the CLI key findings should omit unsupported claims
