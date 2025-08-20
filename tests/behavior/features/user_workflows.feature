@behavior @user_workflows
Feature: User workflows
  As a researcher
  I want to query the system via the CLI
  So I can get answers

  Scenario: CLI search completes successfully
    Given the Autoresearch application is running
    When I run `autoresearch search "workflow test"`
    Then the CLI should exit successfully
