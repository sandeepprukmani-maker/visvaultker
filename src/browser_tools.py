"""
Browser automation tools for smolagents.
These tools allow the AI agent to control a browser via Playwright.
"""

import base64
import io
from typing import Optional
from PIL import Image
from smolagents import tool
from playwright.sync_api import sync_playwright, Browser, Page, BrowserContext

_browser: Optional[Browser] = None
_context: Optional[BrowserContext] = None
_page: Optional[Page] = None
_playwright = None


def get_browser_state():
    """Get current browser state for tools."""
    global _browser, _context, _page, _playwright
    return _playwright, _browser, _context, _page


def set_browser_state(playwright, browser, context, page):
    """Set browser state from external initialization."""
    global _browser, _context, _page, _playwright
    _playwright = playwright
    _browser = browser
    _context = context
    _page = page


@tool
def navigate_to_url(url: str) -> str:
    """
    Navigate the browser to a specific URL.
    
    Args:
        url: The URL to navigate to (e.g., 'https://google.com')
        
    Returns:
        A message indicating success or failure
    """
    global _page
    if _page is None:
        return "Error: Browser not initialized. Please start the browser first."
    
    try:
        _page.goto(url, wait_until="domcontentloaded", timeout=30000)
        return f"Successfully navigated to {url}. Page title: {_page.title()}"
    except Exception as e:
        return f"Error navigating to {url}: {str(e)}"


@tool
def click_element(selector: str) -> str:
    """
    Click on an element in the page using a CSS selector.
    
    Args:
        selector: CSS selector for the element to click (e.g., 'button.submit', '#login-btn', 'a[href="/about"]')
        
    Returns:
        A message indicating success or failure
    """
    global _page
    if _page is None:
        return "Error: Browser not initialized."
    
    try:
        _page.click(selector, timeout=10000)
        _page.wait_for_load_state("domcontentloaded", timeout=10000)
        return f"Successfully clicked element: {selector}"
    except Exception as e:
        return f"Error clicking element {selector}: {str(e)}"


@tool
def click_text(text: str) -> str:
    """
    Click on an element containing specific visible text.
    
    Args:
        text: The visible text of the element to click (e.g., 'Sign In', 'Submit', 'Learn More')
        
    Returns:
        A message indicating success or failure
    """
    global _page
    if _page is None:
        return "Error: Browser not initialized."
    
    try:
        _page.get_by_text(text, exact=False).first.click(timeout=10000)
        _page.wait_for_load_state("domcontentloaded", timeout=10000)
        return f"Successfully clicked element with text: '{text}'"
    except Exception as e:
        return f"Error clicking element with text '{text}': {str(e)}"


@tool
def type_text(selector: str, text: str) -> str:
    """
    Type text into an input field or textarea.
    
    Args:
        selector: CSS selector for the input element (e.g., 'input[name="email"]', '#search-box', 'textarea.comment')
        text: The text to type into the element
        
    Returns:
        A message indicating success or failure
    """
    global _page
    if _page is None:
        return "Error: Browser not initialized."
    
    try:
        _page.fill(selector, text, timeout=10000)
        return f"Successfully typed '{text}' into {selector}"
    except Exception as e:
        return f"Error typing into {selector}: {str(e)}"


@tool
def type_in_focused(text: str) -> str:
    """
    Type text using keyboard into the currently focused element.
    
    Args:
        text: The text to type
        
    Returns:
        A message indicating success or failure
    """
    global _page
    if _page is None:
        return "Error: Browser not initialized."
    
    try:
        _page.keyboard.type(text)
        return f"Successfully typed '{text}'"
    except Exception as e:
        return f"Error typing: {str(e)}"


@tool
def press_key(key: str) -> str:
    """
    Press a keyboard key (Enter, Tab, Escape, etc.).
    
    Args:
        key: The key to press (e.g., 'Enter', 'Tab', 'Escape', 'ArrowDown', 'Backspace')
        
    Returns:
        A message indicating success or failure
    """
    global _page
    if _page is None:
        return "Error: Browser not initialized."
    
    try:
        _page.keyboard.press(key)
        return f"Successfully pressed key: {key}"
    except Exception as e:
        return f"Error pressing key {key}: {str(e)}"


@tool
def scroll_page(direction: str, amount: int = 500) -> str:
    """
    Scroll the page up or down.
    
    Args:
        direction: Direction to scroll ('up' or 'down')
        amount: Pixels to scroll (default 500)
        
    Returns:
        A message indicating success or failure
    """
    global _page
    if _page is None:
        return "Error: Browser not initialized."
    
    try:
        scroll_amount = -amount if direction.lower() == "up" else amount
        _page.mouse.wheel(0, scroll_amount)
        return f"Successfully scrolled {direction} by {amount} pixels"
    except Exception as e:
        return f"Error scrolling: {str(e)}"


@tool
def get_page_content() -> str:
    """
    Get the text content of the current page (useful for understanding what's on the page).
    
    Returns:
        The visible text content of the page (truncated if too long)
    """
    global _page
    if _page is None:
        return "Error: Browser not initialized."
    
    try:
        content = _page.inner_text("body")
        if len(content) > 5000:
            content = content[:5000] + "\n... [content truncated]"
        return f"Page title: {_page.title()}\nURL: {_page.url}\n\nPage content:\n{content}"
    except Exception as e:
        return f"Error getting page content: {str(e)}"


@tool
def get_page_elements() -> str:
    """
    Get a list of interactive elements on the page (buttons, links, inputs).
    This helps identify what can be clicked or interacted with.
    
    Returns:
        A formatted list of interactive elements with their selectors
    """
    global _page
    if _page is None:
        return "Error: Browser not initialized."
    
    try:
        elements = []
        
        buttons = _page.query_selector_all("button")
        for i, btn in enumerate(buttons[:20]):
            text = btn.inner_text().strip()[:50]
            if text:
                elements.append(f"Button: '{text}' - selector: button:nth-of-type({i+1})")
        
        links = _page.query_selector_all("a[href]")
        for i, link in enumerate(links[:20]):
            text = link.inner_text().strip()[:50]
            href = link.get_attribute("href")
            if text:
                elements.append(f"Link: '{text}' -> {href}")
        
        inputs = _page.query_selector_all("input, textarea")
        for i, inp in enumerate(inputs[:20]):
            inp_type = inp.get_attribute("type") or "text"
            name = inp.get_attribute("name") or inp.get_attribute("id") or f"input-{i}"
            placeholder = inp.get_attribute("placeholder") or ""
            elements.append(f"Input ({inp_type}): name='{name}' placeholder='{placeholder}'")
        
        if not elements:
            return "No interactive elements found on the page."
        
        return "Interactive elements on page:\n" + "\n".join(elements)
    except Exception as e:
        return f"Error getting page elements: {str(e)}"


@tool
def take_screenshot() -> str:
    """
    Take a screenshot of the current page state.
    
    Returns:
        A message indicating the screenshot was taken and saved
    """
    global _page
    if _page is None:
        return "Error: Browser not initialized."
    
    try:
        screenshot_bytes = _page.screenshot()
        with open("screenshot.png", "wb") as f:
            f.write(screenshot_bytes)
        return f"Screenshot saved to screenshot.png. Current URL: {_page.url}, Title: {_page.title()}"
    except Exception as e:
        return f"Error taking screenshot: {str(e)}"


@tool
def wait_for_element(selector: str, timeout: int = 10000) -> str:
    """
    Wait for an element to appear on the page.
    
    Args:
        selector: CSS selector for the element to wait for
        timeout: Maximum time to wait in milliseconds (default 10000)
        
    Returns:
        A message indicating if the element appeared or timed out
    """
    global _page
    if _page is None:
        return "Error: Browser not initialized."
    
    try:
        _page.wait_for_selector(selector, timeout=timeout)
        return f"Element {selector} is now visible on the page"
    except Exception as e:
        return f"Element {selector} did not appear within {timeout}ms: {str(e)}"


@tool
def go_back() -> str:
    """
    Navigate back to the previous page in browser history.
    
    Returns:
        A message indicating success and the new page URL
    """
    global _page
    if _page is None:
        return "Error: Browser not initialized."
    
    try:
        _page.go_back(wait_until="domcontentloaded", timeout=10000)
        return f"Navigated back. Now at: {_page.url}"
    except Exception as e:
        return f"Error going back: {str(e)}"


@tool
def refresh_page() -> str:
    """
    Refresh the current page.
    
    Returns:
        A message indicating the page was refreshed
    """
    global _page
    if _page is None:
        return "Error: Browser not initialized."
    
    try:
        _page.reload(wait_until="domcontentloaded", timeout=30000)
        return f"Page refreshed. Title: {_page.title()}"
    except Exception as e:
        return f"Error refreshing page: {str(e)}"


def get_all_browser_tools():
    """Return a list of all browser tools for the agent."""
    return [
        navigate_to_url,
        click_element,
        click_text,
        type_text,
        type_in_focused,
        press_key,
        scroll_page,
        get_page_content,
        get_page_elements,
        take_screenshot,
        wait_for_element,
        go_back,
        refresh_page,
    ]
