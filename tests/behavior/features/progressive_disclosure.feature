Feature: Progressive Disclosure Controls
  As a user of the CLI interface
  I want fine-grained control over which sections are displayed
  So that I can customize the output to my specific needs

  Background:
    Given the Autoresearch application is running

  Scenario: Show available sections for a depth level
    When I run `autoresearch search "test query" --depth standard --show-sections`
    Then I should see a list of available sections for the standard depth
    And each section should be clearly labeled
    And the list should match the standard depth configuration

  Scenario: Include specific sections in output
    When I run `autoresearch search "test query" --depth concise --include=reasoning`
    Then the output should include the reasoning section
    And the output should still respect the concise depth limits for other sections
    And sections not explicitly included should follow the depth default

  Scenario: Exclude specific sections from output
    When I run `autoresearch search "test query" --depth trace --exclude=raw_response`
    Then the output should not include the raw response section
    And all other trace sections should still be included
    And the exclusion should only affect the specified section

  Scenario: Combine include and exclude options
    When I run `autoresearch search "test query" --depth standard --include=metrics --exclude=citations`
    Then the output should include metrics section
    And the output should exclude citations section
    And other standard sections should follow the depth default

  Scenario: Section control with different depth levels
    When I run `autoresearch search "test query" --depth tldr --include=key_findings`
    Then the output should include key findings even though tldr normally excludes them
    And the output should still be limited to tldr-appropriate content for other sections

  Scenario: Section control validation
    When I run `autoresearch search "test query" --include=nonexistent_section`
    Then I should receive an error message about the invalid section name
    And the error should suggest valid section names
    And the command should exit with an error code

  Scenario: Section control with bare mode
    When I run `autoresearch search "test query" --bare-mode --depth standard --include=metrics`
    Then the output should be in bare mode format
    And the included sections should still be present
    And the output should use plain text labels

  Scenario: Section control persistence in session
    When I run `autoresearch search "test query" --depth standard --include=metrics`
    Then the section preferences should be remembered for subsequent queries
    And I should be able to run another query with the same section preferences

  Scenario: Reset section preferences
    When I run `autoresearch search "test query" --depth standard --reset-sections`
    Then all section customizations should be cleared
    And subsequent queries should use default depth settings
