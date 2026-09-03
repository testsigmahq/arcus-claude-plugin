package web.Pages;

import org.openqa.selenium.WebElement;
import org.openqa.selenium.support.FindBy;

public class PutawayPage {

    @FindBy(id = "putaway-confirm")
    private WebElement confirmButton;

    private final SearchPage searchPage;

    public PutawayPage(SearchPage searchPage) {
        this.searchPage = searchPage;
    }

    // One level of delegation. Reading this method alone shows two actions.
    // The true sequence is five, because searchForLpn is itself four, including
    // a conditional. Stopping at the first method opened gets this wrong.
    public void putAwayLpn(String lpn) {
        searchPage.searchForLpn(lpn);
        confirmButton.click();
    }
}
