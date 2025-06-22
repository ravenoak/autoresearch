Feature: Search Local Sources
  As a researcher
  I want to query local files and repositories
  So that I can reference my offline materials

  Scenario: Searching a directory for text files
    Given a directory with text files
    When I search the directory for "hello"
    Then I should get results from the text files

  Scenario: Searching a directory for PDF and DOCX files
    Given a directory with PDF and DOCX files
    When I search the directory for "hello"
    Then I should get results from the PDF and DOCX files

  Scenario: Searching a local Git repository for code snippets or commit messages
    Given a local Git repository with commits containing "TODO"
    When I search the repository for "TODO"
    Then I should see results referencing commit messages or code

  Scenario: Searching commit diffs and metadata in a local Git repository
    Given a local Git repository with diffs containing "FIXME"
    When I search the repository for "FIXME"
    Then I should see commit diff results with metadata
