Feature: Agent System Improvements
  As a developer
  I want the agent system to be well-structured and maintainable
  So that it's easy to add new agents and modify existing ones

  Scenario: Common agent functionality
    Given I have multiple agent implementations
    When I examine their code
    Then common functionality should be extracted to base classes or mixins
    And each agent should only implement its unique behavior

  Scenario: Improved prompt templates
    Given I have an agent that generates prompts
    When the agent creates a prompt
    Then the prompt should include relevant context
    And the prompt should provide clear guidance
    And the prompt should be tailored to the specific agent role

  Scenario: Prompt template system
    Given I have a prompt template system
    When I need to create a prompt for an agent
    Then I should be able to use a template with placeholders
    And the template should be loaded from a configuration file
    And the template should support variable substitution

  Scenario: Agent-specific configuration validation
    Given I have agent-specific configuration
    When I load the configuration
    Then the system should validate the configuration
    And report specific errors for invalid configuration
    And provide helpful suggestions for fixing configuration issues