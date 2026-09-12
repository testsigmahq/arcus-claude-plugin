package web.Pages;

import org.openqa.selenium.WebElement;
import org.openqa.selenium.support.FindBy;

public class ReceivingPage {

    @FindBy(xpath = "//select[@name='reasonCode']")
    private WebElement reasonCodeField;

    @FindBy(id = "reason-submit")
    private WebElement reasonSubmit;

    // "Select" implies a commit. This only types. Nothing is submitted here,
    // and reasonSubmit is never clicked by any caller.
    public void selectReasonCode(String reasonCode) {
        reasonCodeField.sendKeys(reasonCode);
    }
}
