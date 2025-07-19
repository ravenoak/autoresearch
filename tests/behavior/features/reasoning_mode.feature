Feature: Reasoning Mode Selection
  As a user
  I want to choose how the system reasons
  So that agent execution adapts accordingly

  Background:
    Given loops is set to 2 in configuration

  Scenario: Direct mode runs Synthesizer only
    Given reasoning mode is "direct"
    When I run the orchestrator on query "mode test"
    Then the loops used should be 1
    And the agent groups should be "Synthesizer"
    Then the agents executed should be "Synthesizer"

  Scenario: Chain-of-thought mode loops Synthesizer
    Given reasoning mode is "chain-of-thought"
    When I run the orchestrator on query "mode test"
    Then the loops used should be 2
    And the agent groups should be "Synthesizer; Contrarian; FactChecker"
    Then the agents executed should be "Synthesizer, Synthesizer"

  Scenario: Dialectical mode with custom Primus start
    Given loops is set to 1 in configuration
    And reasoning mode is "dialectical"
    And primus start is 1
    When I run the orchestrator on query "mode test"
    Then the loops used should be 1
    And the agent groups should be "Synthesizer; Contrarian; FactChecker"
    Then the agents executed should be "Contrarian, FactChecker, Synthesizer"
