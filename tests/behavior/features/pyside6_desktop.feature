@requires_ui
Feature: PySide6 desktop Phase 1 workflow
  As a Rapid Explorer evaluating the Phase 1 desktop shell
  I want to launch the PySide6 interface and run a query
  So that I can confirm baseline parity with the legacy Streamlit flow

  Background:
    Given the PySide6 desktop runtime is stubbed

  Scenario: Launching the PySide6 desktop shell
    When I launch the PySide6 desktop shell
    Then the desktop main window is shown
    And the QApplication event loop starts

  Scenario: Submitting a query and reviewing results
    When I launch the PySide6 desktop shell
    And I submit "climate resilience" through the desktop query panel
    Then the desktop query controls are disabled while the query runs
    And the orchestrator receives the submitted query
    And I see the synthesized desktop results
