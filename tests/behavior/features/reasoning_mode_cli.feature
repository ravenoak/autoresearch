@behavior
Feature: Reasoning mode via CLI
  As a user
  I want to override reasoning mode on the command line
  So that agent execution adapts accordingly

  Scenario: Direct mode via CLI
    Given loops is set to 2 in configuration
    When I run `autoresearch search "mode test" --mode direct`
    Then the CLI should exit successfully
    And the loops used should be 1
    And the agent groups should be "Synthesizer"
    And the agents executed should be "Synthesizer"
