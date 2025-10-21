@requires_ui @user_workflows
Feature: Textual terminal dashboard opt-in
  The CLI exposes an optional Textual dashboard that surfaces orchestration
  status, metrics, and knowledge graph context without regressing automation
  contracts.

  Background:
    Given the CLI accessibility mode is disabled
    And telemetry capture is enabled

  Scenario: Launch dashboard inside an interactive TTY
    When I run "autoresearch search --tui" inside a TTY session
    And I provide the question "dialectical ux"
    Then the Textual dashboard panels stream orchestration progress
    And telemetry records a "cli.tui.launch" event with tty_detected true
    And exiting the dashboard restores the terminal session cleanly

  Scenario: Fallback when TTY detection fails
    When I run "autoresearch search --tui" without a TTY
    And I provide the question "ux fallback"
    Then the CLI prints a guidance message about the plain workflow
    And telemetry records a "cli.tui.fallback" event with bare_mode false
    And the search command completes using the legacy Typer prompts
