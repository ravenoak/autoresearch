@behavior @reasoning_modes
@behavior @reasoning_modes
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

  Scenario: audit badges propagate to response payloads
    When a reasoning mode "dialectical" is chosen
    And an audit badge "supported" is produced
    And an audit badge "needs_review" is produced
    And the response payload is assembled
    Then the response payload lists the audit badge "supported"
    And the response payload lists the audit badge "needs_review"

  Scenario: AUTO gate telemetry exposes coverage decisions
    Given loops is set to 2 in configuration
    And the planner proposes verification tasks
    And the scout metadata includes adaptive search strategy signals
    When I run the auto planner cycle for query "gate telemetry"
    Then the AUTO gate telemetry should include coverage ratios and outcomes

