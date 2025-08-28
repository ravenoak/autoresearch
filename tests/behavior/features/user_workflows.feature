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
