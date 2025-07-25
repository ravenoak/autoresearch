Feature: Adaptive Output Formatting
  As a user or automation tool
  I want the CLI output to adapt between Markdown/plaintext for TTY and JSON for non-TTY or with a flag
  So that humans get readable answers and machines get schema-validated JSON

  Background:
    Given the application is running

  Scenario: Default TTY output
    When I run `autoresearch search "Test formatting"` in TTY mode
    Then the output should be in Markdown with sections `# Answer`, `## Citations`, `## Reasoning`, and `## Metrics`

  Scenario: Piped output defaults to JSON
    When I run `autoresearch search "Test formatting" | cat`
    Then the output should be valid JSON with keys `answer`, `citations`, `reasoning`, and `metrics`

  Scenario: Explicit JSON flag
    When I run `autoresearch search "Test formatting" --output json`
    Then the output should be valid JSON regardless of terminal context

  Scenario: Explicit Markdown flag
    When I run `autoresearch search "Test formatting" --output markdown`
    Then the output should be Markdown-formatted as in TTY mode
