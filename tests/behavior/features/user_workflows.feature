@behavior @user_workflows
Feature: User workflows
  As a researcher
  I want to query the system via the CLI
  So I can get answers

  Scenario: CLI search completes successfully
    Given the Autoresearch application is running
    When I run `autoresearch search "workflow test"`
    Then the CLI should exit successfully

  Scenario: CLI search with invalid backend reports error
    Given the Autoresearch application is running
    When I run `autoresearch search --backend missing "workflow test"`
    Then the CLI should report an error

  @requires_ui
  Scenario: Streamlit interface displays results
    Given the Streamlit application is running
    When I run a query in the Streamlit interface
    Then the results should be displayed in a tabbed interface

  Scenario: Layered UX exposes claim toggles and prompts
    Given a layered depth payload with claim audits
    When I derive layered UX guidance
    Then the layered payload exposes claim toggles
    And Socratic prompts include claim follow-ups

  Scenario: AUTO reasoning workflow surfaces planner and routing telemetry
    Given loops is set to 2 in configuration
    And reasoning mode is "auto"
    And the planner proposes verification tasks
    When I run the AUTO reasoning CLI for query "workflow auto telemetry rehearsal"
    Then the CLI scout gate decision should escalate to debate
    And the AUTO metrics should include planner depth and routing deltas
