Feature: CLI Output Clarity and Consistency
  As a user of the CLI interface
  I want clean, non-duplicated output with clear formatting
  So that I can easily understand and act on the results

  Background:
    Given the Autoresearch application is running

  Scenario: Success message appears exactly once before results
    When I run `autoresearch search "test query"`
    Then success message "Query processed successfully" should appear exactly once
    And it should appear before the main results output
    And no duplicate success messages should be present

  Scenario: Error messages appear exactly once with clear context
    When I run `autoresearch search "invalid query"`
    Then error message should appear exactly once in the structured output
    And it should include the error description
    And it should include actionable suggestions
    And no duplicate error messages should be present in either stdout or stderr

  Scenario: Progress indicators clear properly
    When I run `autoresearch search "long query"` with progress display
    Then progress bars should appear during execution
    And progress indicators should clear when complete
    And no progress artifacts should remain after completion
    And progress should not interfere with final output

  Scenario: Output streams are properly separated
    When I run `autoresearch search "test query"`
    Then application results should go to stdout
    And diagnostic logs should go to stderr (when not suppressed)
    And error messages should go to stderr
    And status messages should go to stderr

  Scenario: No mixed output streams
    When I run `autoresearch search "test query" 2>&1`
    Then stderr and stdout should be properly separated
    And human-readable content should not be mixed with JSON logs
    And each stream should contain appropriate content type

  Scenario: Bare mode removes decorative elements
    When I run `autoresearch search "test query" --bare-mode`
    Then output should contain no Unicode symbols (✓, ✗, ⚠, ℹ)
    And output should contain no ANSI color codes
    And output should use plain text labels (SUCCESS, ERROR, WARNING, INFO)
    And all functionality should be preserved
    And formatting should be purely textual

  Scenario: Output uniqueness across command types
    When I run `autoresearch search "test query"`
    And I run `autoresearch reverify "state_id"`
    Then each command should produce unique, non-duplicated output
    And success/error messages should not repeat across different commands
    And each command should have its own distinct output pattern

  Scenario: Error message consistency across commands
    When I trigger configuration errors in different commands
    Then error messages should be consistent in format and content
    And error suggestions should be contextual to the specific command
    And error codes should be consistent where applicable

  Scenario: Help text clarity and completeness
    When I run `autoresearch --help`
    Then help text should be clearly formatted and easy to read
    And option descriptions should be concise and actionable
    And examples should be provided where helpful
    And all new options (--log-format, --quiet-logs, --bare-mode) should be documented
