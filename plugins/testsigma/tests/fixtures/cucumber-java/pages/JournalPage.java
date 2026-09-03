package web.Pages;

import org.openqa.selenium.WebElement;
import org.openqa.selenium.support.FindBy;

public class JournalPage {

    @FindBy(id = "journal-refresh")
    private WebElement refreshButton;

    @FindBy(id = "journal-filter")
    private WebElement filterInput;

    @FindBy(css = "table.journal tbody tr")
    private List<WebElement> journalRows;

    // Named like a wait. Is a loop that re-drives the interface on every pass:
    // it retypes the filter and clicks refresh, so flattening it to a passive
    // wait changes what the test does.
    public void refreshUntilRecordAppears(String filter) {
        for (int attempt = 0; attempt < 10; attempt++) {
            if (!journalRows.isEmpty()) {
                return;
            }
            filterInput.clear();
            filterInput.sendKeys(filter);
            refreshButton.click();
        }
        throw new AssertionError("record never appeared");
    }
}
