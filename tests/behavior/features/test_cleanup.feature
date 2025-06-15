Feature: Test Cleanup
  As a developer
  I want to ensure that all tests clean up their side effects
  So that tests don't interfere with each other

  Scenario: Orchestrator and agents integration tests clean up properly
    Given the system is configured with multiple agents
    When I run a query with the dialectical reasoning mode
    Then all monkeypatches should be properly cleaned up
    And all mocks should be properly cleaned up
    And all temporary files should be properly cleaned up