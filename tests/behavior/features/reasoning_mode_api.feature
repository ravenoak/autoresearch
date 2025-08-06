@behavior
Feature: Reasoning mode via API
  As a user
  I want to specify reasoning mode in API requests
  So that agent execution adapts accordingly

  Background:
    Given the API server is running

  Scenario: Direct mode via API
    Given loops is set to 2 in configuration
    When I send a query "mode test" with reasoning mode "direct" to the API
    Then the response status should be 200
    And the loops used should be 1
    And the agent groups should be "Synthesizer"
    And the agents executed should be "Synthesizer"

  Scenario: Chain-of-thought mode via API
    Given loops is set to 2 in configuration
    When I send a query "mode test" with reasoning mode "chain-of-thought" to the API
    Then the response status should be 200
    And the loops used should be 2
    And the agent groups should be "Synthesizer; Contrarian; FactChecker"
    And the agents executed should be "Synthesizer, Synthesizer"

  Scenario: Dialectical mode via API
    Given loops is set to 1 in configuration
    When I send a query "mode test" with reasoning mode "dialectical" to the API
    Then the response status should be 200
    And the loops used should be 1
    And the agent groups should be "Synthesizer; Contrarian; FactChecker"
    And the agents executed should be "Synthesizer, Contrarian, FactChecker"
