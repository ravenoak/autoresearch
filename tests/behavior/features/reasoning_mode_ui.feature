@behavior @reasoning_modes @requires_ui
Feature: Reasoning mode selection in UI
  As a user
  I want to select a reasoning mode via the UI
  So that the system adapts its execution style

  Scenario Outline: choosing reasoning mode in the UI
    Given the Streamlit application is running
    When a reasoning mode "<mode>" is chosen
    Then bdd_context records mode "<mode>"

    Examples:
      | mode        |
      | direct      |
      | dialectical |
