@behavior @error_recovery
Feature: Error recovery workflow
  As a developer
  I want transient errors to trigger recovery
  So the system can resume operation

  Scenario: Transient error triggers recovery
    Given a transient error occurs
    When the orchestrator executes the query "fail once"
    Then bdd_context should record "recovery_applied" as true

  Scenario: Persistent error fails without recovery
    Given a persistent error occurs
    When the orchestrator executes the query "fail always"
    Then bdd_context should record "recovery_applied" as false
