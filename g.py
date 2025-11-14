import re
from playwright.sync_api import Playwright, sync_playwright, expect

def run(playwright: Playwright):
    browser = playwright.chromium.launch(headless=False)
    page = browser.new_page()

    page.goto("https://practicetestautomation.com/practice-test-login/")
    page.get_by_label("Username").fill("student")
    page.get_by_label("Password").fill("Password123")
    page.get_by_role("button", name="Submit").click()

    expect(page).to_have_url(re.compile(".*practicetestautomation.com/logged-in-successfully/"))

    # ✔ regex must be re.compile()
    expect(page.get_by_text(re.compile("Congratulations|successfully logged in"))).to_be_visible()

    expect(page.get_by_role("link", name="Log out")).to_be_visible()

    browser.close()

with sync_playwright() as playwright:
    run(playwright)
