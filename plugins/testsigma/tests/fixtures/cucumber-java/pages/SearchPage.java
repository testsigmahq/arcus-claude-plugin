package web.Pages;

import org.openqa.selenium.WebElement;
import org.openqa.selenium.support.FindBy;

public class SearchPage {

    @FindBy(id = "lpn-search-input")
    private WebElement lpnSearchInput;

    @FindBy(css = ".search-panel .expand-toggle")
    private WebElement expandToggle;

    // Reads as one action in the feature file. Performs four.
    public void searchForLpn(String lpn) {
        if (!lpnSearchInput.isDisplayed()) {
            expandToggle.click();
        }
        lpnSearchInput.clear();
        lpnSearchInput.sendKeys(lpn);
        lpnSearchInput.sendKeys(Keys.ENTER);
    }
}
