@behavior @reasoning_modes @requires_vss
Feature: Reasoning mode with VSS extension
  Scenario Outline: reasoning mode uses VSS extension
    Given I have a valid configuration with VSS extension enabled
    And reasoning mode is "<mode>"
    When I run the orchestrator on query "mode test"
    Then the VSS extension should be loaded from the filesystem

    Examples:
      | mode        |
      | dialectical |
      | direct      |
