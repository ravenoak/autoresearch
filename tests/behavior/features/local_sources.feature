Feature: Search Local Sources
  As a researcher
  I want to query local files and repositories
  So that I can reference my offline materials

  Scenario: Searching a directory for text files
    Given a directory with text files
    When I search the directory for "hello"
    Then I should get results from the text files

  Scenario: Searching a local Git repository for code snippets or commit messages
    Given a local Git repository with commits containing "TODO"
    When I search the repository for "TODO"
    Then I should see results referencing commit messages or code
