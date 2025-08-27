Feature: Backup roundtrip
  Scenario: Create then list backups
    When I run `autoresearch config backup create --dir backups`
    And I run `autoresearch config backup list --dir backups`
    Then the backup directory should contain a backup file
