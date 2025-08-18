Feature: Search CLI
  Scenarios covering the search command

  # Spec: docs/specs/search.md#key-behaviors - Execute search queries via the CLI
  Scenario: Run a basic search query
    When I run `autoresearch search "What is artificial intelligence?" --reasoning-mode direct`
    Then the CLI should exit successfully

  # Spec: docs/specs/search.md#key-behaviors - Execute search queries via the CLI
  Scenario: Missing query argument
    When I run `autoresearch search`
    Then the CLI should exit with an error
