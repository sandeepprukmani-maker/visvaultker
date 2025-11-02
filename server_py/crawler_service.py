import asyncio
import base64
import time
from playwright.async_api import async_playwright, Browser, BrowserContext, Page
from typing import Optional, List, Dict, Set
from urllib.parse import urljoin, urlparse
from datetime import datetime
import urllib.robotparser

class CrawlerService:
    def __init__(self):
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.current_proxy: Optional[str] = None
        self.rate_limit_delay = 1.0
        self.robots_cache: Dict[str, urllib.robotparser.RobotFileParser] = {}

    async def initialize(self, options: Optional[dict] = None):
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
                    "--disable-setuid-sandbox",
                    "--disable-web-security"
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

    async def can_fetch(self, url: str, respect_robots: bool = True) -> bool:
        if not respect_robots:
            return True
            
        try:
            parsed = urlparse(url)
            robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
            
            if robots_url not in self.robots_cache:
                rp = urllib.robotparser.RobotFileParser()
                rp.set_url(robots_url)
                parse_success = False
                
                try:
                    page = await self.context.new_page() if self.context else None
                    if page:
                        response = await page.goto(robots_url, wait_until="domcontentloaded", timeout=5000)
                        if response and response.ok:
                            robots_txt = await response.text()
                            rp.parse(robots_txt.splitlines())
                            parse_success = True
                        await page.close()
                except Exception as e:
                    print(f"Error fetching robots.txt from {robots_url}: {e}")
                
                if parse_success:
                    self.robots_cache[robots_url] = rp
                else:
                    return True
            
            rp = self.robots_cache.get(robots_url)
            if rp:
                return rp.can_fetch("*", url)
            return True
        except Exception as e:
            print(f"Error checking robots.txt: {e}")
            return True

    async def crawl_website(self, start_url: str, options: Optional[dict] = None) -> List[Dict]:
        options = options or {}
        depth = options.get("depth", 3)
        wait_time = options.get("waitTime", 2000)
        screenshot_quality = options.get("screenshotQuality", 80)
        max_pages = options.get("maxPages", 100)
        enable_dynamic_discovery = options.get("dynamicDiscovery", True)
        respect_robots = options.get("respectRobots", True)
        
        crawl_delay = options.get("crawlDelay")
        if crawl_delay:
            self.rate_limit_delay = float(crawl_delay)

        await self.initialize(options)

        visited_urls: Set[str] = set()
        pages_data: List[Dict] = []
        queue = [{"url": start_url, "currentDepth": 0}]
        last_request_time = 0.0

        while queue and len(pages_data) < max_pages:
            item = queue.pop(0)
            url = item["url"]
            current_depth = item["currentDepth"]

            if url in visited_urls or current_depth > depth:
                continue
            
            if not await self.can_fetch(url, respect_robots):
                print(f"Robots.txt disallows: {url}")
                continue

            visited_urls.add(url)

            elapsed = time.time() - last_request_time
            if elapsed < self.rate_limit_delay:
                await asyncio.sleep(self.rate_limit_delay - elapsed)

            try:
                page = await self.context.new_page()
                
                await page.goto(url, wait_until="networkidle", timeout=30000)
                
                await self.smart_wait(page, wait_time)
                
                if enable_dynamic_discovery:
                    await self.discover_dynamic_content(page)
                
                await self.handle_infinite_scroll(page)
                
                title = await page.title()
                
                screenshot = await page.screenshot(type="jpeg", quality=screenshot_quality, full_page=False)
                screenshot_base64 = f"data:image/jpeg;base64,{base64.b64encode(screenshot).decode()}"

                elements = await self.extract_all_elements(page)
                
                iframe_elements = await self.extract_iframe_content(page)
                elements.extend(iframe_elements)
                
                links = []
                if current_depth < depth:
                    links = await self.extract_links(page)

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
                last_request_time = time.time()

            except Exception as error:
                print(f"Error crawling {url}: {error}")
                continue

        return pages_data

    async def smart_wait(self, page: Page, base_wait: int = 2000):
        await asyncio.wait_for(page.wait_for_load_state("networkidle"), timeout=10)
        
        await page.wait_for_timeout(base_wait)
        
        try:
            await page.wait_for_function(
                "() => document.readyState === 'complete'",
                timeout=5000
            )
        except:
            pass

        await self.wait_for_dom_stable(page)

    async def wait_for_dom_stable(self, page: Page, timeout: int = 5000):
        try:
            await page.evaluate(f"""
                new Promise((resolve) => {{
                    let timeoutId;
                    const observer = new MutationObserver(() => {{
                        clearTimeout(timeoutId);
                        timeoutId = setTimeout(() => {{
                            observer.disconnect();
                            resolve();
                        }}, 500);
                    }});
                    
                    observer.observe(document.body, {{
                        childList: true,
                        subtree: true
                    }});
                    
                    setTimeout(() => {{
                        observer.disconnect();
                        resolve();
                    }}, {timeout});
                }});
            """)
        except:
            pass

    async def discover_dynamic_content(self, page: Page):
        try:
            interactive_patterns = await page.evaluate("""
                () => {
                    const patterns = [];
                    
                    const tabs = document.querySelectorAll('[role="tab"], .tab, [data-toggle="tab"]');
                    tabs.forEach(tab => {
                        if (tab.offsetParent && !tab.getAttribute('aria-selected')) {
                            patterns.push({type: 'tab', element: tab});
                        }
                    });
                    
                    const accordions = document.querySelectorAll('[role="button"][aria-expanded="false"], .accordion-toggle, summary');
                    accordions.forEach(acc => {
                        if (acc.offsetParent) {
                            patterns.push({type: 'accordion', element: acc});
                        }
                    });
                    
                    const dropdowns = document.querySelectorAll('.dropdown-toggle, [data-toggle="dropdown"]');
                    dropdowns.forEach(dd => {
                        if (dd.offsetParent) {
                            patterns.push({type: 'dropdown', element: dd});
                        }
                    });
                    
                    const modals = document.querySelectorAll('[data-toggle="modal"], [data-bs-toggle="modal"]');
                    modals.forEach(modal => {
                        if (modal.offsetParent) {
                            patterns.push({type: 'modal', element: modal});
                        }
                    });
                    
                    return patterns.slice(0, 10).map((p, idx) => ({
                        type: p.type,
                        selector: p.element.id ? '#' + p.element.id : 
                                 p.element.className ? '.' + Array.from(p.element.classList).join('.') :
                                 p.element.tagName.toLowerCase(),
                        index: idx
                    }));
                }
            """)
            
            for pattern in interactive_patterns:
                try:
                    selector = pattern["selector"]
                    elements = await page.query_selector_all(selector)
                    
                    if pattern["index"] < len(elements):
                        element = elements[pattern["index"]]
                        
                        if pattern["type"] in ["tab", "accordion", "dropdown"]:
                            await element.click()
                            await page.wait_for_timeout(500)
                            await self.wait_for_dom_stable(page, 2000)
                            
                except Exception as e:
                    continue
                    
        except Exception as error:
            print(f"Error discovering dynamic content: {error}")

    async def handle_infinite_scroll(self, page: Page, max_scrolls: int = 5):
        try:
            previous_height = await page.evaluate("document.body.scrollHeight")
            
            for _ in range(max_scrolls):
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await page.wait_for_timeout(1000)
                
                new_height = await page.evaluate("document.body.scrollHeight")
                if new_height == previous_height:
                    break
                previous_height = new_height
                
            await page.evaluate("window.scrollTo(0, 0)")
            
        except Exception as error:
            print(f"Error handling infinite scroll: {error}")

    async def extract_all_elements(self, page: Page) -> List[Dict]:
        elements = await page.evaluate("""
            () => {
                const extractedElements = [];
                const interactiveTags = ['button', 'a', 'input', 'select', 'textarea', 'label', 'form'];
                const seen = new Set();
                
                const getXPath = (element) => {
                    if (element.id) return '//*[@id="' + element.id + '"]';
                    if (element === document.body) return '/html/body';
                    
                    let ix = 0;
                    const siblings = element.parentNode?.childNodes || [];
                    for (let i = 0; i < siblings.length; i++) {
                        const sibling = siblings[i];
                        if (sibling === element) {
                            const parentPath = element.parentNode ? getXPath(element.parentNode) : '';
                            return parentPath + '/' + element.tagName.toLowerCase() + '[' + (ix + 1) + ']';
                        }
                        if (sibling.nodeType === 1 && sibling.tagName === element.tagName) {
                            ix++;
                        }
                    }
                    return '';
                };
                
                const extractElement = (el, inShadow = false) => {
                    const tag = el.tagName.toLowerCase();
                    const text = el.textContent?.trim().substring(0, 200) || '';
                    const id = el.id;
                    const classes = Array.from(el.classList).join('.');
                    
                    let selector = tag;
                    if (id) {
                        selector = '#' + id;
                    } else if (classes) {
                        selector = tag + '.' + classes;
                    } else if (el.getAttribute('name')) {
                        selector = tag + '[name="' + el.getAttribute('name') + '"]';
                    }
                    
                    const key = selector + '|' + text.substring(0, 50);
                    if (seen.has(key) && !interactiveTags.includes(tag)) return null;
                    seen.add(key);
                    
                    const attributes = {};
                    for (const attr of el.attributes) {
                        attributes[attr.name] = attr.value;
                    }
                    
                    const style = window.getComputedStyle(el);
                    const isVisible = el.offsetParent !== null || 
                                    (style.position === 'fixed' && style.display !== 'none');
                    
                    return {
                        tag,
                        selector,
                        text,
                        attributes,
                        xpath: getXPath(el),
                        isVisible,
                        isInteractive: interactiveTags.includes(tag),
                        inShadow
                    };
                };
                
                const traverseShadowDOM = (root, inShadow = false) => {
                    root.querySelectorAll('*').forEach((el, idx) => {
                        const tag = el.tagName.toLowerCase();
                        
                        if (interactiveTags.includes(tag)) {
                            const data = extractElement(el, inShadow);
                            if (data) extractedElements.push(data);
                        } else if (idx < 500 && (el.offsetParent || el.tagName === 'BODY')) {
                            const data = extractElement(el, inShadow);
                            if (data) extractedElements.push(data);
                        }
                        
                        if (el.shadowRoot) {
                            traverseShadowDOM(el.shadowRoot, true);
                        }
                    });
                };
                
                traverseShadowDOM(document);
                
                return extractedElements.slice(0, 1000);
            }
        """)
        
        return elements

    async def extract_iframe_content(self, page: Page) -> List[Dict]:
        try:
            iframes = await page.query_selector_all('iframe')
            iframe_elements = []
            
            for i, iframe in enumerate(iframes[:5]):
                try:
                    frame = await iframe.content_frame()
                    if frame:
                        iframe_src = await iframe.get_attribute('src') or ''
                        iframe_id = await iframe.get_attribute('id') or f'iframe-{i}'
                        
                        frame_elements = await frame.evaluate(f"""
                            (frameId) => {{
                                const elements = [];
                                const getXPath = (element) => {{
                                    if (element.id) return '//*[@id="' + element.id + '"]';
                                    let ix = 0;
                                    const siblings = element.parentNode?.childNodes || [];
                                    for (let i = 0; i < siblings.length; i++) {{
                                        const sibling = siblings[i];
                                        if (sibling === element) {{
                                            return element.tagName.toLowerCase() + '[' + (ix + 1) + ']';
                                        }}
                                        if (sibling.nodeType === 1 && sibling.tagName === element.tagName) {{
                                            ix++;
                                        }}
                                    }}
                                    return '';
                                }};
                                
                                document.querySelectorAll('button, a, input, select, textarea, label').forEach(el => {{
                                    const tag = el.tagName.toLowerCase();
                                    const id = el.id;
                                    const classes = Array.from(el.classList).join('.');
                                    
                                    let selector = id ? '#' + id : (classes ? tag + '.' + classes : tag);
                                    
                                    const attributes = {{}};
                                    for (const attr of el.attributes) {{
                                        attributes[attr.name] = attr.value;
                                    }}
                                    
                                    elements.push({{
                                        tag: tag,
                                        selector: 'iframe#' + frameId + ' >> ' + selector,
                                        text: el.textContent?.trim().substring(0, 100) || '',
                                        attributes: attributes,
                                        xpath: getXPath(el),
                                        isVisible: el.offsetParent !== null,
                                        isInteractive: true,
                                        inIframe: true,
                                        iframeSrc: '{iframe_src}'
                                    }});
                                }});
                                return elements.slice(0, 50);
                            }}
                        """, iframe_id)
                        iframe_elements.extend(frame_elements)
                except Exception as e:
                    print(f"Error extracting iframe {i}: {e}")
                    continue
            
            return iframe_elements
        except:
            return []

    async def extract_links(self, page: Page) -> List[str]:
        try:
            links = await page.evaluate("""
                () => {
                    const linkSet = new Set();
                    document.querySelectorAll('a[href]').forEach(a => {
                        const href = a.href;
                        if (href && 
                            !href.startsWith('javascript:') && 
                            !href.startsWith('mailto:') &&
                            !href.startsWith('tel:') &&
                            !href.startsWith('#')) {
                            linkSet.add(href);
                        }
                    });
                    return Array.from(linkSet);
                }
            """)
            return links
        except:
            return []

    async def get_cookies(self) -> List[Dict]:
        if self.context:
            cookies = await self.context.cookies()
            return [dict(c) for c in cookies]
        return []

    async def set_cookies(self, cookies: List[Dict]):
        if self.context:
            await self.context.add_cookies(cookies)

    async def get_local_storage(self, url: str) -> Dict:
        if not self.context:
            return {}
        
        page = await self.context.new_page()
        try:
            await page.goto(url)
            storage = await page.evaluate("""
                () => {
                    const items = {};
                    for (let i = 0; i < localStorage.length; i++) {
                        const key = localStorage.key(i);
                        if (key) {
                            items[key] = localStorage.getItem(key) || '';
                        }
                    }
                    return items;
                }
            """)
            return storage
        finally:
            await page.close()

    async def set_local_storage(self, url: str, storage: Dict):
        if not self.context:
            return
        
        page = await self.context.new_page()
        try:
            await page.goto(url)
            await page.evaluate(f"""
                (storage) => {{
                    Object.entries(storage).forEach(([key, value]) => {{
                        localStorage.setItem(key, value);
                    }});
                }}
            """, storage)
        finally:
            await page.close()

crawler_service = CrawlerService()
