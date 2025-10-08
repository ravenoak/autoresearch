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

  Scenario: Markdown escapes control characters
    When I format a response containing control characters as markdown
    Then the markdown output should fence escaped control sequences

  Scenario: TTY output escapes control characters
    When I run `autoresearch search "Test formatting"` in TTY mode with control characters
    Then the CLI markdown output should include escaped control sequences

  Scenario: Graph output format
    When I run `autoresearch search "Test formatting" --output graph`
    Then the output should include "Knowledge Graph"

  Scenario: Graph export aliases produce canonical payloads
    When I build a depth payload requesting graph exports via aliases
    Then the graph export payload should include canonical formats `graph_json` and `graphml`
