Feature: Orchestration System
  As a developer
  I want a robust and maintainable orchestration system
  So that agent interactions are reliable and easy to debug

  Background:
    Given the system is configured with default settings

  Scenario: Token counting without monkey patching
    When I run a query with token counting enabled
    Then token usage should be recorded correctly
    And no global state should be modified

  Scenario: Extracting complex methods
    When I run a query with multiple agents
    Then the orchestration should handle agent execution in smaller focused methods
    And the code should be more maintainable

  Scenario: Improved error handling
    When an agent fails during execution
    Then the error should be properly captured and categorized
    And the system should recover gracefully
    And detailed error information should be logged

  Scenario: Better logging for debugging
    When I run a query with debug logging enabled
    Then each step of the orchestration process should be logged
    And log messages should include relevant context
    And log levels should be appropriate for the message content