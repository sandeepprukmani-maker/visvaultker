"""
Advanced Browser Automation Features
Provides screenshot capture, PDF generation, cookie management, and more
"""
import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
from browser_use import Browser

logger = logging.getLogger(__name__)


class AdvancedBrowserFeatures:
    """
    Advanced capabilities for browser automation
    Handles screenshots, PDFs, cookies, sessions, and more
    """
    
    def __init__(self, output_dir: str = "automation_outputs"):
        """
        Initialize advanced browser features
        
        Args:
            output_dir: Directory to save screenshots, PDFs, etc.
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        self.screenshots_dir = self.output_dir / "screenshots"
        self.pdfs_dir = self.output_dir / "pdfs"
        self.cookies_dir = self.output_dir / "cookies"
        
        self.screenshots_dir.mkdir(exist_ok=True)
        self.pdfs_dir.mkdir(exist_ok=True)
        self.cookies_dir.mkdir(exist_ok=True)
        
        logger.info(f"📁 Advanced features initialized with output dir: {self.output_dir}")
    
    async def capture_screenshot(self, page, name: Optional[str] = None, full_page: bool = True) -> Dict[str, Any]:
        """
        Capture screenshot of current page
        
        Args:
            page: Playwright page object
            name: Optional custom name for screenshot
            full_page: Capture full scrollable page
            
        Returns:
            Dictionary with screenshot path and metadata
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{name}_{timestamp}.png" if name else f"screenshot_{timestamp}.png"
            filepath = self.screenshots_dir / filename
            
            await page.screenshot(path=str(filepath), full_page=full_page)
            
            logger.info(f"📸 Screenshot saved: {filepath}")
            
            return {
                "success": True,
                "path": str(filepath),
                "filename": filename,
                "full_page": full_page,
                "timestamp": timestamp,
                "url": page.url
            }
        except Exception as e:
            logger.error(f"❌ Screenshot capture failed: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def generate_pdf(self, page, name: Optional[str] = None, 
                          landscape: bool = False, 
                          print_background: bool = True) -> Dict[str, Any]:
        """
        Generate PDF of current page
        
        Args:
            page: Playwright page object
            name: Optional custom name for PDF
            landscape: Use landscape orientation
            print_background: Include background graphics
            
        Returns:
            Dictionary with PDF path and metadata
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{name}_{timestamp}.pdf" if name else f"page_{timestamp}.pdf"
            filepath = self.pdfs_dir / filename
            
            await page.pdf(
                path=str(filepath),
                format='A4',
                landscape=landscape,
                print_background=print_background,
                margin={'top': '20px', 'right': '20px', 'bottom': '20px', 'left': '20px'}
            )
            
            logger.info(f"📄 PDF generated: {filepath}")
            
            return {
                "success": True,
                "path": str(filepath),
                "filename": filename,
                "landscape": landscape,
                "timestamp": timestamp,
                "url": page.url
            }
        except Exception as e:
            logger.error(f"❌ PDF generation failed: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def save_cookies(self, context, session_name: str) -> Dict[str, Any]:
        """
        Save browser cookies for session persistence
        
        Args:
            context: Playwright browser context
            session_name: Name for this session
            
        Returns:
            Dictionary with save status and path
        """
        try:
            cookies = await context.cookies()
            
            filepath = self.cookies_dir / f"{session_name}_cookies.json"
            
            with open(filepath, 'w') as f:
                json.dump(cookies, f, indent=2)
            
            logger.info(f"🍪 Cookies saved: {filepath} ({len(cookies)} cookies)")
            
            return {
                "success": True,
                "path": str(filepath),
                "session_name": session_name,
                "cookie_count": len(cookies)
            }
        except Exception as e:
            logger.error(f"❌ Cookie save failed: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def load_cookies(self, context, session_name: str) -> Dict[str, Any]:
        """
        Load previously saved cookies to restore session
        
        Args:
            context: Playwright browser context
            session_name: Name of session to restore
            
        Returns:
            Dictionary with load status
        """
        try:
            filepath = self.cookies_dir / f"{session_name}_cookies.json"
            
            if not filepath.exists():
                return {
                    "success": False,
                    "error": f"Session '{session_name}' not found"
                }
            
            with open(filepath, 'r') as f:
                cookies = json.load(f)
            
            await context.add_cookies(cookies)
            
            logger.info(f"🍪 Cookies loaded: {filepath} ({len(cookies)} cookies)")
            
            return {
                "success": True,
                "session_name": session_name,
                "cookie_count": len(cookies)
            }
        except Exception as e:
            logger.error(f"❌ Cookie load failed: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_local_storage(self, page) -> Dict[str, Any]:
        """
        Extract localStorage data from page
        
        Args:
            page: Playwright page object
            
        Returns:
            Dictionary with localStorage contents
        """
        try:
            storage_data = await page.evaluate("""() => {
                let data = {};
                for (let i = 0; i < localStorage.length; i++) {
                    let key = localStorage.key(i);
                    data[key] = localStorage.getItem(key);
                }
                return data;
            }""")
            
            logger.info(f"💾 LocalStorage extracted: {len(storage_data)} items")
            
            return {
                "success": True,
                "data": storage_data,
                "item_count": len(storage_data)
            }
        except Exception as e:
            logger.error(f"❌ LocalStorage extraction failed: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def set_local_storage(self, page, data: Dict[str, str]) -> Dict[str, Any]:
        """
        Set localStorage data on page
        
        Args:
            page: Playwright page object
            data: Dictionary of key-value pairs to set
            
        Returns:
            Dictionary with operation status
        """
        try:
            for key, value in data.items():
                await page.evaluate(f"""() => {{
                    localStorage.setItem('{key}', '{value}');
                }}""")
            
            logger.info(f"💾 LocalStorage set: {len(data)} items")
            
            return {
                "success": True,
                "item_count": len(data)
            }
        except Exception as e:
            logger.error(f"❌ LocalStorage set failed: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def list_sessions(self) -> List[str]:
        """
        List all saved cookie sessions
        
        Returns:
            List of session names
        """
        sessions = []
        for file in self.cookies_dir.glob("*_cookies.json"):
            session_name = file.stem.replace("_cookies", "")
            sessions.append(session_name)
        
        return sessions
    
    def cleanup_old_files(self, days: int = 7):
        """
        Clean up old screenshots and PDFs
        
        Args:
            days: Delete files older than this many days
        """
        from datetime import timedelta
        cutoff = datetime.now() - timedelta(days=days)
        
        deleted_count = 0
        for directory in [self.screenshots_dir, self.pdfs_dir]:
            for file in directory.glob("*"):
                if file.stat().st_mtime < cutoff.timestamp():
                    file.unlink()
                    deleted_count += 1
        
        logger.info(f"🗑️  Cleaned up {deleted_count} old files")
        return deleted_count
