Feature: Error Handling
  As a user of Autoresearch
  I want to receive informative and actionable error messages
  So that I can quickly identify and fix issues

  Scenario: Configuration error with invalid reasoning mode
    Given a configuration with an invalid reasoning mode "invalid_mode"
    When I try to load the configuration
    Then I should receive an error message containing "Invalid reasoning mode"
    And the error message should list the valid reasoning modes
    And the error message should suggest how to fix the issue

  Scenario: Storage error with uninitialized components
    Given the storage system is not properly initialized
    When I try to perform a storage operation
    Then I should receive an error message containing the specific component that is not initialized
    And the error message should suggest how to initialize the component

  Scenario: Orchestration error with failed agent
    Given an agent that will fail during execution
    When I run a query that uses this agent
    Then I should receive an error message containing the name of the failed agent
    And the error message should include the specific reason for the failure
    And the error message should suggest possible solutions

  Scenario: LLM error with invalid model
    Given a configuration with an invalid LLM model
    When I try to execute a query
    Then I should receive an error message containing the invalid model name
    And the error message should list the available models
    And the error message should suggest how to configure a valid model

  Scenario: Search error with invalid search backend
    Given a configuration with an invalid search backend
    When I try to perform a search
    Then I should receive an error message containing the invalid backend name
    And the error message should list the available search backends
    And the error message should suggest how to configure a valid backend