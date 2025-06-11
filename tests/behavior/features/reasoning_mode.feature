Feature: Reasoning Mode Selection
  As a user
  I want to choose how the system reasons
  So that agent execution adapts accordingly

  Background:
    Given loops is set to 2 in configuration

  Scenario: Direct mode runs Synthesizer only
    Given reasoning mode is "direct"
    When I run the orchestrator on query "mode test"
    Then the agents executed should be "Synthesizer"

  Scenario: Chain-of-thought mode loops Synthesizer
    Given reasoning mode is "chain-of-thought"
    When I run the orchestrator on query "mode test"
    Then the agents executed should be "Synthesizer, Synthesizer"
