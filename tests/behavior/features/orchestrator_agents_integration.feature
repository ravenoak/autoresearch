Feature: Orchestrator and Agents Integration
  As a user of the Autoresearch system
  I want the orchestrator to properly coordinate multiple agents
  So that I get comprehensive and balanced research results

  Background:
    Given the system is configured with multiple agents
    And the system is using a dummy LLM adapter for testing

  Scenario: Orchestrator executes agents in the correct order
    When I run a query with the dialectical reasoning mode
    Then the agents should be executed in the correct sequence
    And each agent should receive the state from previous agents
    And the final result should include contributions from all agents

  Scenario: Orchestrator handles agent errors gracefully
    Given an agent that will raise an error
    When I run a query with that agent
    Then the orchestrator should catch and log the error
    And the orchestrator should continue with other agents if possible
    And the final result should include information about the error

  Scenario: Orchestrator respects agent execution conditions
    Given an agent that can only execute under specific conditions
    When I run a query that doesn't meet those conditions
    Then that agent should not be executed
    And the orchestrator should continue with other agents
    And the final result should not include contributions from the skipped agent