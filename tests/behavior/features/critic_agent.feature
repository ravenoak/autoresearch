@user_workflows
Feature: Critic agent evaluation
  Scenario: Critic agent produces critique for research findings
    Given a query with findings
    When the critic agent evaluates the query
    Then a critique is produced
