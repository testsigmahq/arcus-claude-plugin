package web.Pages;

import org.openqa.selenium.WebElement;
import org.openqa.selenium.support.FindBy;

public class ArchivePage {

    @FindBy(id = "archive-confirm")
    private WebElement confirmButton;

    private final SearchPage searchPage;

    public ArchivePage(SearchPage searchPage) {
        this.searchPage = searchPage;
    }

    // One level of delegation. Reading this method alone shows two actions.
    // The true sequence is five, because searchForRecord is itself four, including
    // a conditional. Stopping at the first method opened gets this wrong.
    public void archiveRecord(String lpn) {
        searchPage.searchForRecord(lpn);
        confirmButton.click();
    }
}
