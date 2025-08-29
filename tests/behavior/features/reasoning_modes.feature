@behavior @reasoning_modes @requires_nlp
Feature: Basic reasoning modes
  As a developer
  I want to capture selected reasoning modes
  So the orchestrator can adjust execution

  Scenario Outline: selecting a reasoning mode
    When a reasoning mode "<mode>" is chosen
    Then bdd_context records mode "<mode>"

    Examples:
      | mode        |
      | direct      |
      | dialectical |

