"""
Browser Automation Engine with Playwright
Handles browser control, anti-detection, and session management
"""

from playwright.async_api import async_playwright, Browser, Page, BrowserContext
from typing import Optional, Dict, Any, List
import json
import asyncio
from pathlib import Path
import os

class BrowserEngine:
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.contexts: Dict[str, BrowserContext] = {}
        self.pages: Dict[str, Page] = {}
        
        # Storage paths
        self.storage_dir = Path("storage")
        self.sessions_dir = self.storage_dir / "sessions"
        self.screenshots_dir = self.storage_dir / "screenshots"
        
        # Create directories
        self.sessions_dir.mkdir(parents=True, exist_ok=True)
        self.screenshots_dir.mkdir(parents=True, exist_ok=True)
    
    async def initialize(self):
        """Initialize Playwright and browser"""
        self.playwright = await async_playwright().start()
        
        # Launch with stealth mode and anti-detection
        self.browser = await self.playwright.chromium.launch(
            headless=self.headless,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-web-security',
                '--disable-features=IsolateOrigins,site-per-process'
            ]
        )
    
    async def create_context(
        self, 
        context_id: str,
        session_file: Optional[str] = None,
        viewport: Dict[str, int] = None,
        user_agent: Optional[str] = None
    ) -> BrowserContext:
        """Create a new browser context with optional session restoration"""
        
        context_options = {
            'viewport': viewport or {'width': 1920, 'height': 1080},
            'user_agent': user_agent or 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'locale': 'en-US',
            'timezone_id': 'America/New_York',
            'permissions': ['geolocation', 'notifications'],
        }
        
        # Load session if exists
        if session_file and (self.sessions_dir / session_file).exists():
            context_options['storage_state'] = str(self.sessions_dir / session_file)
        
        context = await self.browser.new_context(**context_options)
        
        # Add stealth scripts to avoid detection
        await context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5]
            });
            
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en']
            });
            
            window.chrome = {
                runtime: {}
            };
        """)
        
        self.contexts[context_id] = context
        return context
    
    async def create_page(self, context_id: str, page_id: str) -> Page:
        """Create a new page in the context"""
        if context_id not in self.contexts:
            await self.create_context(context_id)
        
        context = self.contexts[context_id]
        page = await context.new_page()
        
        # Set extra headers to avoid detection
        await page.set_extra_http_headers({
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-User': '?1',
            'Sec-Fetch-Dest': 'document'
        })
        
        self.pages[page_id] = page
        return page
    
    async def navigate(self, page_id: str, url: str, wait_until: str = 'networkidle') -> None:
        """Navigate to a URL"""
        page = self.pages.get(page_id)
        if not page:
            raise ValueError(f"Page {page_id} not found")
        
        await page.goto(url, wait_until=wait_until, timeout=60000)
    
    async def save_session(self, context_id: str, session_name: str) -> str:
        """Save browser session (cookies, localStorage, etc.)"""
        context = self.contexts.get(context_id)
        if not context:
            raise ValueError(f"Context {context_id} not found")
        
        session_path = self.sessions_dir / f"{session_name}.json"
        await context.storage_state(path=str(session_path))
        return str(session_path)
    
    async def take_screenshot(self, page_id: str, name: str, full_page: bool = False) -> str:
        """Take a screenshot of the page"""
        page = self.pages.get(page_id)
        if not page:
            raise ValueError(f"Page {page_id} not found")
        
        screenshot_path = self.screenshots_dir / f"{name}.png"
        await page.screenshot(path=str(screenshot_path), full_page=full_page)
        return str(screenshot_path)
    
    async def execute_script(self, page_id: str, script: str) -> Any:
        """Execute JavaScript on the page"""
        page = self.pages.get(page_id)
        if not page:
            raise ValueError(f"Page {page_id} not found")
        
        return await page.evaluate(script)
    
    async def get_page_content(self, page_id: str) -> str:
        """Get HTML content of the page"""
        page = self.pages.get(page_id)
        if not page:
            raise ValueError(f"Page {page_id} not found")
        
        return await page.content()
    
    async def click(self, page_id: str, selector: str, timeout: int = 30000) -> None:
        """Click an element"""
        page = self.pages.get(page_id)
        if not page:
            raise ValueError(f"Page {page_id} not found")
        
        await page.click(selector, timeout=timeout)
    
    async def fill(self, page_id: str, selector: str, value: str, timeout: int = 30000) -> None:
        """Fill an input field"""
        page = self.pages.get(page_id)
        if not page:
            raise ValueError(f"Page {page_id} not found")
        
        await page.fill(selector, value, timeout=timeout)
    
    async def wait_for_selector(self, page_id: str, selector: str, timeout: int = 30000) -> None:
        """Wait for an element to appear"""
        page = self.pages.get(page_id)
        if not page:
            raise ValueError(f"Page {page_id} not found")
        
        await page.wait_for_selector(selector, timeout=timeout)
    
    async def cleanup(self, page_id: Optional[str] = None, context_id: Optional[str] = None):
        """Cleanup resources"""
        if page_id and page_id in self.pages:
            await self.pages[page_id].close()
            del self.pages[page_id]
        
        if context_id and context_id in self.contexts:
            await self.contexts[context_id].close()
            del self.contexts[context_id]
    
    async def close(self):
        """Close all resources"""
        for page in self.pages.values():
            await page.close()
        
        for context in self.contexts.values():
            await context.close()
        
        if self.browser:
            await self.browser.close()
        
        if self.playwright:
            await self.playwright.stop()

# Global instance
browser_engine = BrowserEngine(headless=os.getenv('BROWSER_HEADLESS', 'true').lower() == 'true')
