import asyncio
import yaml
from typing import Dict, List, Optional, Any
from playwright.async_api import async_playwright, Page, Browser, BrowserContext
import base64
import json

class BrowserAutomation:
    def __init__(self, config_path: str = "config.yaml"):
        import os
        if not os.path.exists(config_path):
            config_path = os.path.join(os.path.dirname(__file__), "..", "config.yaml")
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        self.browser_settings = self.config["browser_settings"]
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
    
    async def initialize(self):
        self.playwright = await async_playwright().start()
        
        self.browser = await self.playwright.chromium.launch(
            headless=self.browser_settings["headless"],
            args=[
                '--disable-blink-features=AutomationControlled',
                '--no-sandbox',
                '--disable-dev-shm-usage'
            ]
        )
        
        self.context = await self.browser.new_context(
            viewport={
                "width": self.browser_settings["viewport"]["width"],
                "height": self.browser_settings["viewport"]["height"]
            },
            user_agent=self.browser_settings["user_agent"]
        )
        
        if self.browser_settings["stealth_mode"]:
            await self.context.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
            """)
        
        self.page = await self.context.new_page()
        self.page.set_default_timeout(self.browser_settings["timeout"])
    
    async def navigate(self, url: str) -> Dict[str, Any]:
        if not self.page:
            await self.initialize()
        
        try:
            response = await self.page.goto(url, wait_until="networkidle")
            
            return {
                "success": True,
                "url": self.page.url,
                "title": await self.page.title(),
                "status": response.status if response else None
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_page_content(self) -> str:
        if not self.page:
            raise Exception("Browser not initialized")
        return await self.page.content()
    
    async def take_screenshot(self, full_page: bool = False) -> str:
        if not self.page:
            raise Exception("Browser not initialized")
        
        screenshot_bytes = await self.page.screenshot(full_page=full_page)
        return base64.b64encode(screenshot_bytes).decode('utf-8')
    
    async def find_elements(self, selector: str) -> List[Dict[str, Any]]:
        if not self.page:
            raise Exception("Browser not initialized")
        
        elements = await self.page.query_selector_all(selector)
        
        results = []
        for elem in elements:
            try:
                results.append({
                    "tag": await elem.evaluate("el => el.tagName"),
                    "text": await elem.text_content(),
                    "visible": await elem.is_visible(),
                    "attributes": await elem.evaluate("el => Object.fromEntries(Array.from(el.attributes).map(a => [a.name, a.value]))")
                })
            except:
                continue
        
        return results
    
    async def click_element(self, selector: str) -> Dict[str, Any]:
        if not self.page:
            raise Exception("Browser not initialized")
        
        try:
            await self.page.click(selector, timeout=5000)
            await self.page.wait_for_load_state("networkidle")
            
            return {
                "success": True,
                "action": "click",
                "selector": selector
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "action": "click",
                "selector": selector
            }
    
    async def hover_element(self, selector: str) -> Dict[str, Any]:
        if not self.page:
            raise Exception("Browser not initialized")
        
        try:
            await self.page.hover(selector, timeout=5000)
            await asyncio.sleep(0.5)
            
            return {
                "success": True,
                "action": "hover",
                "selector": selector
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "action": "hover",
                "selector": selector
            }
    
    async def fill_input(self, selector: str, value: str) -> Dict[str, Any]:
        if not self.page:
            raise Exception("Browser not initialized")
        
        try:
            await self.page.fill(selector, value, timeout=5000)
            
            return {
                "success": True,
                "action": "fill",
                "selector": selector,
                "value": value
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "action": "fill",
                "selector": selector
            }
    
    async def scroll_page(self, direction: str = "down", amount: int = 500) -> Dict[str, Any]:
        if not self.page:
            raise Exception("Browser not initialized")
        
        try:
            if direction == "down":
                await self.page.evaluate(f"window.scrollBy(0, {amount})")
            elif direction == "up":
                await self.page.evaluate(f"window.scrollBy(0, -{amount})")
            
            await asyncio.sleep(0.5)
            
            return {
                "success": True,
                "action": "scroll",
                "direction": direction,
                "amount": amount
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "action": "scroll"
            }
    
    async def extract_dom_structure(self) -> Dict[str, Any]:
        if not self.page:
            raise Exception("Browser not initialized")
        
        dom_data = await self.page.evaluate("""
            () => {
                function getElementInfo(el) {
                    return {
                        tag: el.tagName.toLowerCase(),
                        id: el.id || null,
                        classes: Array.from(el.classList),
                        text: el.textContent ? el.textContent.trim().substring(0, 100) : '',
                        attributes: Object.fromEntries(
                            Array.from(el.attributes).map(a => [a.name, a.value])
                        ),
                        bounds: el.getBoundingClientRect().toJSON(),
                        visible: el.offsetParent !== null,
                        interactive: ['A', 'BUTTON', 'INPUT', 'SELECT', 'TEXTAREA'].includes(el.tagName)
                    };
                }
                
                function traverseDOM(el, depth = 0, maxDepth = 5) {
                    if (depth > maxDepth) return null;
                    
                    const info = getElementInfo(el);
                    info.children = [];
                    
                    for (let child of el.children) {
                        const childInfo = traverseDOM(child, depth + 1, maxDepth);
                        if (childInfo) {
                            info.children.push(childInfo);
                        }
                    }
                    
                    return info;
                }
                
                return traverseDOM(document.body);
            }
        """)
        
        return dom_data
    
    async def find_interactive_elements(self) -> List[Dict[str, Any]]:
        if not self.page:
            raise Exception("Browser not initialized")
        
        elements = await self.page.evaluate("""
            () => {
                const interactive = document.querySelectorAll('a, button, input, select, textarea, [onclick], [role="button"]');
                return Array.from(interactive).map((el, idx) => ({
                    index: idx,
                    tag: el.tagName.toLowerCase(),
                    type: el.type || null,
                    id: el.id || null,
                    classes: Array.from(el.classList),
                    text: el.textContent ? el.textContent.trim().substring(0, 50) : '',
                    href: el.href || null,
                    visible: el.offsetParent !== null,
                    bounds: el.getBoundingClientRect().toJSON(),
                    selector: el.id ? `#${el.id}` : el.className ? `.${Array.from(el.classList).join('.')}` : el.tagName.toLowerCase()
                }));
            }
        """)
        
        return [el for el in elements if el['visible']]
    
    async def wait_for_selector(self, selector: str, timeout: int = 5000) -> bool:
        if not self.page:
            raise Exception("Browser not initialized")
        
        try:
            await self.page.wait_for_selector(selector, timeout=timeout)
            return True
        except:
            return False
    
    async def execute_script(self, script: str) -> Any:
        if not self.page:
            raise Exception("Browser not initialized")
        
        return await self.page.evaluate(script)
    
    async def get_cookies(self) -> List[Dict[str, Any]]:
        if not self.context:
            raise Exception("Browser context not initialized")
        
        return await self.context.cookies()
    
    async def set_cookies(self, cookies: List[Dict[str, Any]]):
        if not self.context:
            raise Exception("Browser context not initialized")
        
        await self.context.add_cookies(cookies)
    
    async def close(self):
        if self.page:
            await self.page.close()
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
