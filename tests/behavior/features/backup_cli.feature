Feature: Backup CLI
  Scenario: Create backup
    Given a temporary work directory
    When I run `autoresearch config backup create --dir backups`
    Then the backup directory should contain a backup file
