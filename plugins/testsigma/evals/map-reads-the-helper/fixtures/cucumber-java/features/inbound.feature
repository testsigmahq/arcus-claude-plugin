Feature: Inbound receiving

  Background:
    Given I am signed in

  Scenario: Receive a single record
    When I search for record "REC05ALPHA"
    Then I see the record "REC05ALPHA" in the list
    When I select "Damaged" reason code
    Then I see the record "REC05ALPHA" in the list

  Scenario: Archive a record
    When I archive record "REC05ALPHA"
    Then I see the record "REC05ALPHA" in the list

  Scenario Outline: Receive several records
    When I search for record <record>
    Then I see the record <record> in the list

    Examples:
      | record |
      | A1  |
      | A2  |
