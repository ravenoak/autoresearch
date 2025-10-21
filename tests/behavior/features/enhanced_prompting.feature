@requires_ui @user_workflows
Feature: Enhanced prompt-toolkit integration
  Prompt interactions supply history, completions, and multi-line editing when
  the terminal supports prompt-toolkit while preserving Typer fallbacks.

  Background:
    Given prompt-toolkit is installed
    And the CLI accessibility mode is disabled

  Scenario: Use enhanced prompt features inside a TTY
    When I start "autoresearch search --interactive" inside a TTY session
    And I press the up arrow after entering "first draft query"
    Then the previous query appears in the prompt history
    And tab completion suggests agent names from the current roster
    And telemetry records a "cli.prompt.enhanced" event

  Scenario: Fall back to Typer prompts when prompt-toolkit is unavailable
    Given prompt-toolkit cannot be imported
    When I start "autoresearch search --interactive" without a TTY
    Then the CLI uses the baseline Typer prompt helpers
    And telemetry records a "cli.prompt.basic" event
