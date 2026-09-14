package web.Pages;

import org.openqa.selenium.WebElement;
import org.openqa.selenium.support.FindBy;

public class SearchPage {

    @FindBy(id = "record-search-input")
    private WebElement recordSearchInput;

    @FindBy(css = ".search-panel .expand-toggle")
    private WebElement expandToggle;

    // Reads as one action in the feature file. Performs four.
    public void searchForRecord(String lpn) {
        if (!recordSearchInput.isDisplayed()) {
            expandToggle.click();
        }
        recordSearchInput.clear();
        recordSearchInput.sendKeys(lpn);
        recordSearchInput.sendKeys(Keys.ENTER);
    }
}
