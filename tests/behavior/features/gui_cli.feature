Feature: GUI CLI
  Scenarios for launching the Streamlit GUI

  Scenario: Launch GUI without opening a browser
    When I run `autoresearch gui --port 8502 --no-browser`
    Then the CLI should exit successfully

  Scenario: Display help for GUI command
    When I run `autoresearch gui --help`
    Then the CLI should exit successfully

  Scenario: Launch GUI with invalid port
    When I run `autoresearch gui --port not-a-number`
    Then the CLI should exit with an error
