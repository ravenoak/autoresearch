Feature: Backup CLI
  Scenario: Create backup
    Given a temporary work directory
    When I run `autoresearch config backup create --dir backups`
    Then the backup directory should contain a backup file

  Scenario: List backups
    Given a temporary work directory
    When I run `autoresearch config backup list --dir backups`
    Then the CLI should exit successfully

  Scenario: Restore backup
    Given a temporary work directory
    And a dummy backup file "backups/test.tar"
    When I run `autoresearch config backup restore backups/test.tar --dir restore --force`
    Then the CLI should exit successfully
