Feature: Inbound receiving

  Background:
    Given I am signed in

  Scenario: Receive a single pallet
    When I search for LPN "ILPN05INT26"
    Then I see the LPN "ILPN05INT26" in the list
    When I select "Damaged" reason code
    Then I see the LPN "ILPN05INT26" in the list

  Scenario: Put away a pallet
    When I put away LPN "ILPN05INT26"
    Then I see the LPN "ILPN05INT26" in the list

  Scenario Outline: Receive several pallets
    When I search for LPN <lpn>
    Then I see the LPN <lpn> in the list

    Examples:
      | lpn |
      | A1  |
      | A2  |
