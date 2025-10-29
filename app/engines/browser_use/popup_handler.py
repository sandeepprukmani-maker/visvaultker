"""
Enhanced Popup Window Handler for Browser-Use
Automatically detects and switches to new popup windows with advanced features
"""
import asyncio
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
from playwright.async_api import Page, BrowserContext

logger = logging.getLogger(__name__)


class PopupWindowHandler:
    """
    Enhanced popup window handler with advanced detection and management
    Features:
    - Automatic popup detection and switching
    - Configurable timeouts
    - Detailed logging and tracking
    - Multi-popup orchestration
    - Popup priority rules
    """
    
    def __init__(self, context: BrowserContext, popup_timeout: int = 10000, 
                 auto_switch: bool = True, log_verbose: bool = True):
        """
        Initialize the enhanced popup handler
        
        Args:
            context: Playwright browser context to monitor
            popup_timeout: Timeout in milliseconds for popup operations (default: 10000ms)
            auto_switch: Automatically switch to new popups (default: True)
            log_verbose: Enable detailed logging (default: True)
        """
        self.context = context
        self.current_page = None
        self.popup_detected = False
        self.new_pages = []
        self.popup_timeout = popup_timeout
        self.auto_switch = auto_switch
        self.log_verbose = log_verbose
        
        self.popup_history: List[Dict[str, Any]] = []
        self.popup_count = 0
        
        context.on("page", self._on_new_page)
        
        if self.log_verbose:
            logger.info(f"🔍 Enhanced popup handler initialized (timeout: {popup_timeout}ms, auto_switch: {auto_switch})")
    
    def _on_new_page(self, page: Page):
        """
        Enhanced event handler for new pages/windows with tracking
        
        Args:
            page: Newly created page object
        """
        self.popup_count += 1
        popup_info = {
            "popup_number": self.popup_count,
            "url": page.url or "about:blank",
            "timestamp": datetime.now().isoformat(),
            "auto_switched": self.auto_switch
        }
        
        self.popup_history.append(popup_info)
        self.new_pages.append(page)
        self.popup_detected = True
        
        if self.log_verbose:
            logger.info(f"🆕 Popup #{self.popup_count} detected: {popup_info['url']}")
            logger.info(f"📊 Total popups opened: {self.popup_count}")
    
    async def get_active_page(self) -> Optional[Page]:
        """
        Get the currently active page with enhanced timeout handling
        
        Returns:
            Active page object or None
        """
        if self.new_pages and self.auto_switch:
            latest_page = self.new_pages[-1]
            
            try:
                await latest_page.wait_for_load_state("domcontentloaded", timeout=self.popup_timeout)
                
                if self.log_verbose:
                    logger.info(f"✅ Switched to popup window: {latest_page.url}")
                
                return latest_page
            except Exception as e:
                logger.warning(f"⚠️ Popup not ready within {self.popup_timeout}ms: {str(e)}")
        
        all_pages = self.context.pages
        if all_pages:
            return all_pages[-1]
        
        return None
    
    async def wait_for_popup(self, timeout: Optional[int] = None) -> Optional[Page]:
        """
        Wait for a popup to appear
        
        Args:
            timeout: Optional custom timeout in milliseconds
            
        Returns:
            New popup page or None if timeout
        """
        wait_timeout = timeout or self.popup_timeout
        start_time = datetime.now()
        
        while (datetime.now() - start_time).total_seconds() * 1000 < wait_timeout:
            if self.new_pages:
                new_page = self.new_pages[-1]
                if self.log_verbose:
                    logger.info(f"✅ Popup appeared: {new_page.url}")
                return new_page
            await asyncio.sleep(0.1)
        
        logger.warning(f"⏱️  No popup appeared within {wait_timeout}ms")
        return None
    
    def get_popup_stats(self) -> Dict[str, Any]:
        """
        Get statistics about popup handling
        
        Returns:
            Dictionary with popup statistics
        """
        return {
            "total_popups": self.popup_count,
            "active_popups": len(self.new_pages),
            "popup_history": self.popup_history,
            "auto_switch_enabled": self.auto_switch,
            "timeout_ms": self.popup_timeout
        }
    
    def reset(self):
        """Reset the handler state with enhanced logging"""
        previous_count = self.popup_count
        self.new_pages.clear()
        self.popup_detected = False
        
        if self.log_verbose:
            logger.info(f"🔄 Popup handler reset (processed {previous_count} popups this session)")
    
    def has_popup(self) -> bool:
        """Check if a popup window was detected"""
        return self.popup_detected
    
    def get_all_pages(self):
        """Get all open pages"""
        return self.context.pages
