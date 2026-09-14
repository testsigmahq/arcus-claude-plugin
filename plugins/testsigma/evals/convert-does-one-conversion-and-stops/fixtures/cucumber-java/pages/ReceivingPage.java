package web.Pages;

import org.openqa.selenium.WebElement;
import org.openqa.selenium.support.FindBy;

public class ReceivingPage {

    @FindBy(xpath = "//select[@name='reasonCode']")
    private WebElement reasonCodeField;

    @FindBy(id = "reason-submit")
    private WebElement reasonSubmit;

    @FindBy(id = "print-label")
    private WebElement printLabel;

    // "Select" implies a commit. This only types. Nothing is submitted here,
    // and reasonSubmit is never clicked by any caller.
    public void selectReasonCode(String reasonCode) {
        reasonCodeField.sendKeys(reasonCode);
    }

    // Hands off to the browser's own print dialogue, which is not part of the
    // application under test. Nothing after this click is a web control.
    public void printReceivingLabel() {
        printLabel.click();
    }
}
