"""
Browser Resource Cleanup Utilities
Ensures browser instances are properly closed even on errors
"""
import logging
import asyncio
from contextlib import asynccontextmanager
from typing import Optional

logger = logging.getLogger(__name__)


class BrowserCleanupManager:
    """
    Manager for browser resource cleanup.
    Ensures all browser instances and pages are properly closed.
    """
    
    def __init__(self):
        self._active_browsers = []
        self._active_pages = []
    
    def register_browser(self, browser):
        """Register an active browser instance"""
        if browser not in self._active_browsers:
            self._active_browsers.append(browser)
            logger.debug(f"Registered browser instance (total: {len(self._active_browsers)})")
    
    def register_page(self, page):
        """Register an active page instance"""
        if page not in self._active_pages:
            self._active_pages.append(page)
            logger.debug(f"Registered page instance (total: {len(self._active_pages)})")
    
    async def cleanup_page(self, page):
        """Cleanup a specific page"""
        try:
            if page in self._active_pages:
                await page.close()
                self._active_pages.remove(page)
                logger.debug("Page closed successfully")
        except Exception as e:
            logger.warning(f"Error closing page: {e}")
    
    async def cleanup_browser(self, browser):
        """Cleanup a specific browser"""
        try:
            if browser in self._active_browsers:
                await browser.close()
                self._active_browsers.remove(browser)
                logger.debug("Browser closed successfully")
        except Exception as e:
            logger.warning(f"Error closing browser: {e}")
    
    async def cleanup_all(self):
        """Force cleanup of all registered resources"""
        logger.info(f"🧹 Cleaning up {len(self._active_pages)} pages and {len(self._active_browsers)} browsers")
        
        # Close all pages first
        for page in list(self._active_pages):
            await self.cleanup_page(page)
        
        # Then close all browsers
        for browser in list(self._active_browsers):
            await self.cleanup_browser(browser)
        
        logger.info("✅ Cleanup complete")


@asynccontextmanager
async def managed_browser(browser_factory, cleanup_manager: Optional[BrowserCleanupManager] = None):
    """
    Context manager for browser instances with automatic cleanup.
    
    Usage:
        async with managed_browser(browser_factory, cleanup_manager) as browser:
            # Use browser
            pass
        # Browser automatically closed
    
    Args:
        browser_factory: Async function that creates a browser instance
        cleanup_manager: Optional cleanup manager to register with
    """
    browser = None
    try:
        browser = await browser_factory()
        if cleanup_manager:
            cleanup_manager.register_browser(browser)
        yield browser
    except Exception as e:
        logger.error(f"Error in browser context: {e}")
        raise
    finally:
        if browser:
            try:
                await browser.close()
                if cleanup_manager and browser in cleanup_manager._active_browsers:
                    cleanup_manager._active_browsers.remove(browser)
                logger.debug("Browser closed via context manager")
            except Exception as e:
                logger.warning(f"Error closing browser in context manager: {e}")


@asynccontextmanager
async def managed_page(page_factory, cleanup_manager: Optional[BrowserCleanupManager] = None):
    """
    Context manager for page instances with automatic cleanup.
    
    Usage:
        async with managed_page(page_factory, cleanup_manager) as page:
            # Use page
            pass
        # Page automatically closed
    
    Args:
        page_factory: Async function that creates a page instance
        cleanup_manager: Optional cleanup manager to register with
    """
    page = None
    try:
        page = await page_factory()
        if cleanup_manager:
            cleanup_manager.register_page(page)
        yield page
    except Exception as e:
        logger.error(f"Error in page context: {e}")
        raise
    finally:
        if page:
            try:
                await page.close()
                if cleanup_manager and page in cleanup_manager._active_pages:
                    cleanup_manager._active_pages.remove(page)
                logger.debug("Page closed via context manager")
            except Exception as e:
                logger.warning(f"Error closing page in context manager: {e}")
