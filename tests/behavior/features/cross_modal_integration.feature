Feature: Cross-Modal Integration
  As a user of multiple Autoresearch interfaces
  I want consistent behavior across all interfaces
  So that I can switch between interfaces seamlessly

  Background:
    Given the Autoresearch system is running

  Scenario: Shared Query History
    When I execute a query "What is the capital of France?" via CLI
    And I open the Streamlit GUI
    Then the query history should include "What is the capital of France?"
    And I should be able to rerun the query from the GUI
    And the results should be consistent with the CLI results

  Scenario: Consistent Error Handling
    When I execute an invalid query via CLI
    Then I should receive a specific error message
    When I execute the same invalid query via GUI
    Then I should receive the same error message in the GUI

  Scenario: Configuration Synchronization
    When I update the configuration via CLI
    And I open the Streamlit GUI
    Then the GUI should reflect the updated configuration
    When I update the configuration via GUI
    And I check the configuration via CLI
    Then the CLI should show the updated configuration

  Scenario: A2A Interface Consistency
    When I execute a query via the A2A interface
    Then the response format should match the CLI response format
    And the response should contain the same fields as the GUI response
    And the error handling should be consistent with other interfaces

  Scenario: MCP Interface Consistency
    When I execute a query via the MCP interface
    Then the response format should match the CLI response format
    And the response should contain the same fields as the GUI response
    And the error handling should be consistent with other interfaces