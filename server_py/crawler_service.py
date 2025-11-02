import asyncio
import base64
from playwright.async_api import async_playwright, Browser, BrowserContext, Page
from typing import Optional
from urllib.parse import urljoin, urlparse

class CrawlerService:
    def __init__(self):
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.current_proxy: Optional[str] = None

    async def initialize(self, options: dict = None):
        options = options or {}
        new_proxy = str(options.get("proxy")) if options.get("proxy") else None
        proxy_changed = self.current_proxy != new_proxy

        if proxy_changed or not self.browser:
            await self.close()
            
            playwright = await async_playwright().start()
            launch_options = {
                "headless": True,
                "args": [
                    "--disable-blink-features=AutomationControlled",
                    "--disable-dev-shm-usage",
                    "--no-sandbox",
                    "--disable-setuid-sandbox"
                ]
            }

            if options.get("proxy"):
                launch_options["proxy"] = options["proxy"]

            self.browser = await playwright.chromium.launch(**launch_options)
            self.current_proxy = new_proxy

        if self.context:
            await self.context.close()

        context_options = {
            "viewport": options.get("viewport", {"width": 1920, "height": 1080}),
            "user_agent": options.get("userAgent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"),
            "java_script_enabled": options.get("javascript", True),
            "ignore_https_errors": True
        }

        self.context = await self.browser.new_context(**context_options)

        if options.get("cookies"):
            await self.context.add_cookies(options["cookies"])

        await self.context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)

    async def close(self):
        if self.context:
            await self.context.close()
            self.context = None
        if self.browser:
            await self.browser.close()
            self.browser = None

    async def crawl_website(self, start_url: str, options: dict = None) -> list[dict]:
        options = options or {}
        depth = options.get("depth", 3)
        wait_time = options.get("waitTime", 1000)
        screenshot_quality = options.get("screenshotQuality", 80)

        await self.initialize(options)

        visited_urls = set()
        pages_data = []
        queue = [{"url": start_url, "currentDepth": 0}]

        while queue and len(pages_data) < 100:
            item = queue.pop(0)
            url = item["url"]
            current_depth = item["currentDepth"]

            if url in visited_urls or current_depth > depth:
                continue

            visited_urls.add(url)

            try:
                page = await self.context.new_page()
                await page.goto(url, wait_until="networkidle", timeout=30000)
                await page.wait_for_timeout(wait_time)

                title = await page.title()
                
                screenshot = await page.screenshot(type="jpeg", quality=screenshot_quality)
                screenshot_base64 = f"data:image/jpeg;base64,{base64.b64encode(screenshot).decode()}"

                elements = await self.extract_elements(page)
                
                links = []
                if current_depth < depth:
                    links = await page.evaluate("""() => {
                        return Array.from(document.querySelectorAll('a[href]'))
                            .map(a => a.href)
                            .filter(href => href && !href.startsWith('javascript:') && !href.startsWith('mailto:'));
                    }""")

                pages_data.append({
                    "url": url,
                    "title": title,
                    "screenshot": screenshot_base64,
                    "elements": elements
                })

                base_domain = urlparse(start_url).netloc
                for link in links:
                    parsed = urlparse(link)
                    if parsed.netloc == base_domain and link not in visited_urls:
                        queue.append({"url": link, "currentDepth": current_depth + 1})

                await page.close()

            except Exception as error:
                print(f"Error crawling {url}: {error}")
                continue

        return pages_data

    async def extract_elements(self, page: Page) -> list[dict]:
        elements = await page.evaluate("""() => {
            const extractedElements = [];
            const interactiveTags = ['button', 'a', 'input', 'select', 'textarea'];
            
            document.querySelectorAll('*').forEach((el, idx) => {
                if (!el.offsetParent && el.tagName !== 'BODY') return;
                
                const tag = el.tagName.toLowerCase();
                if (!interactiveTags.includes(tag) && idx > 200) return;
                
                const text = el.textContent?.trim().substring(0, 100) || '';
                const id = el.id;
                const classes = Array.from(el.classList).join('.');
                
                let selector = tag;
                if (id) selector = `#${id}`;
                else if (classes) selector = `${tag}.${classes}`;
                
                const attributes = {};
                for (const attr of el.attributes) {
                    attributes[attr.name] = attr.value;
                }
                
                extractedElements.push({
                    tag,
                    selector,
                    text,
                    attributes,
                    xpath: null
                });
            });
            
            return extractedElements.slice(0, 500);
        }""")
        
        return elements

    async def get_cookies(self) -> list[dict]:
        if self.context:
            return await self.context.cookies()
        return []

    async def set_cookies(self, cookies: list[dict]):
        if self.context:
            await self.context.add_cookies(cookies)

    async def get_local_storage(self, url: str) -> dict:
        if not self.context:
            return {}
        
        page = await self.context.new_page()
        try:
            await page.goto(url)
            storage = await page.evaluate("""() => {
                const items = {};
                for (let i = 0; i < localStorage.length; i++) {
                    const key = localStorage.key(i);
                    if (key) {
                        items[key] = localStorage.getItem(key) || '';
                    }
                }
                return items;
            }""")
            return storage
        finally:
            await page.close()

crawler_service = CrawlerService()
