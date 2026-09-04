# Fixture: Cucumber over a Java page-object layer

A deliberately small source suite in the shape the `cucumber-java` Source Adapter
reads. Hand-built. Contains no data from any real suite.

It is small but not simple: each page object below carries one of the faults the
adapter exists to warn about, so a reader who trusts the feature file alone gets
each one wrong.

| Page object | The trap |
|---|---|
| `SearchPage.searchForLpn` | Does **more** than its step line implies: expands a hidden field, clears it, types, presses Enter |
| `ReceivingPage.selectReasonCode` | Does **less** than its step line implies: sends text and never submits |
| `JournalPage.refreshUntilRecordAppears` | Is a **loop** that re-drives the interface, not a passive wait |
| `PutawayPage.putAwayLpn` | **Delegates** to another page object, so the true sequence is only visible one level down |

Locators live in `@FindBy` annotations on the page objects, which is what makes
this source one that carries locators.
