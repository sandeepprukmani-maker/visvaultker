"""
Seed test for Playwright Test Agents
Provides a ready-to-use page context for test generation
"""
from playwright.sync_api import Page, expect


def test_seed(page: Page):
    """
    Seed test that sets up the environment for Playwright Test Agents
    
    This test:
    - Navigates to the application
    - Provides a ready-to-use page object
    - Serves as an example for generated tests
    """
    # Navigate to the application
    page.goto("http://localhost:5000")
    
    # Wait for page to be ready
    page.wait_for_load_state("networkidle")
    
    # Basic verification
    expect(page).to_have_url("http://localhost:5000")
