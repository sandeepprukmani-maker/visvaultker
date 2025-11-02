import asyncio
import base64
from playwright.async_api import async_playwright, Browser, BrowserContext, Page
from typing import Optional
from datetime import datetime

class AutomationService:
    def __init__(self):
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.current_proxy: Optional[str] = None
        self.current_headless: bool = True

    async def initialize(self, options: dict = None):
        options = options or {}
        headless = options.get("headless", True)
        new_proxy = str(options.get("proxy")) if options.get("proxy") else None
        proxy_changed = self.current_proxy != new_proxy
        headless_changed = self.current_headless != headless

        if proxy_changed or headless_changed or not self.browser:
            await self.close()
            
            playwright = await async_playwright().start()
            launch_options = {
                "headless": headless,
                "args": [
                    "--disable-blink-features=AutomationControlled",
                    "--disable-dev-shm-usage",
                    "--no-sandbox"
                ]
            }

            if options.get("proxy"):
                launch_options["proxy"] = options["proxy"]

            self.browser = await playwright.chromium.launch(**launch_options)
            self.current_proxy = new_proxy
            self.current_headless = headless

        if self.context:
            await self.context.close()

        context_options = {
            "viewport": {"width": 1920, "height": 1080},
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
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

    async def execute_automation(self, automation_id: str, steps: list[dict], options: dict = None) -> dict:
        options = options or {}
        start_time = datetime.now()
        logs = []
        extracted_data = {}

        await self.initialize(options)
        page = await self.context.new_page()

        if options.get("localStorage"):
            await page.add_init_script(f"""
                (storage => {{
                    Object.entries(storage).forEach(([key, value]) => {{
                        localStorage.setItem(key, value);
                    }});
                }})({options["localStorage"]})
            """)

        if options.get("sessionStorage"):
            await page.add_init_script(f"""
                (storage => {{
                    Object.entries(storage).forEach(([key, value]) => {{
                        sessionStorage.setItem(key, value);
                    }});
                }})({options["sessionStorage"]})
            """)

        try:
            for i, step in enumerate(steps):
                step_start = datetime.now()
                status = "success"
                details = None

                if step.get("waitBefore"):
                    await page.wait_for_timeout(step["waitBefore"])

                try:
                    result = await self.execute_step_with_retry(page, step, options)
                    
                    if result and isinstance(result, dict):
                        extracted_data.update(result)

                    if options.get("screenshot") or step["action"] in ["click", "navigate", "verify"]:
                        screenshot = await page.screenshot(type="jpeg", quality=70)
                        details = f"data:image/jpeg;base64,{base64.b64encode(screenshot).decode()}"
                except Exception as error:
                    status = "error"
                    details = str(error)

                logs.append({
                    "automationId": automation_id,
                    "action": step.get("description", step["action"]),
                    "status": status,
                    "details": details,
                    "screenshot": details if details and details.startswith("data:image") else None
                })

                if status == "error":
                    raise Exception(f"Step {i + 1} failed: {step.get('description', step['action'])}")

            duration = int((datetime.now() - start_time).total_seconds() * 1000)
            await page.close()

            return {
                "success": True,
                "duration": duration,
                "logs": logs,
                "data": extracted_data if extracted_data else None
            }
        except Exception as error:
            duration = int((datetime.now() - start_time).total_seconds() * 1000)
            await page.close()

            return {
                "success": False,
                "duration": duration,
                "logs": logs,
                "error": str(error)
            }

    async def execute_step_with_retry(self, page: Page, step: dict, options: dict) -> any:
        max_retries = step.get("retryCount", options.get("maxRetries", 3))
        retry_delay = options.get("retryDelay", 1000)
        last_error = None

        for attempt in range(max_retries + 1):
            try:
                if attempt > 0:
                    await page.wait_for_timeout(retry_delay * (2 ** (attempt - 1)))
                
                return await self.execute_step(page, step, options)
            except Exception as error:
                last_error = error
                
                if attempt < max_retries and step.get("fallbackSelectors"):
                    step["selector"] = step["fallbackSelectors"][attempt % len(step["fallbackSelectors"])]
                    print(f"Retrying with fallback selector: {step['selector']}")
                elif attempt < max_retries:
                    print(f"Retry attempt {attempt + 1}/{max_retries} for: {step.get('description')}")

        raise last_error

    async def execute_step(self, page: Page, step: dict, options: dict) -> any:
        action = step["action"]

        if action == "navigate":
            if step.get("value"):
                url = step["value"] if step["value"].startswith("http") else f"{options.get('baseUrl', '')}{step['value']}"
                await page.goto(url, wait_until="networkidle", timeout=30000)
                await page.wait_for_timeout(1000)

        elif action == "click":
            if step.get("selector"):
                element = await self.find_element_with_fallback(page, step)
                if not element:
                    raise Exception(f"Element not found: {step['selector']}")
                await element.click()
                await page.wait_for_timeout(500)

        elif action == "type":
            if step.get("selector") and step.get("value") is not None:
                element = await self.find_element_with_fallback(page, step)
                if not element:
                    raise Exception(f"Element not found: {step['selector']}")
                await element.fill(step["value"])
                await page.wait_for_timeout(300)

        elif action == "select":
            if step.get("selector") and step.get("value") is not None:
                element = await self.find_element_with_fallback(page, step)
                if not element:
                    raise Exception(f"Element not found: {step['selector']}")
                await element.select_option(step["value"])
                await page.wait_for_timeout(300)

        elif action == "wait":
            wait_time = int(step.get("value", "1000"))
            await page.wait_for_timeout(wait_time)

        elif action == "waitForElement":
            if step.get("selector"):
                timeout = int(step["value"]) if step.get("value") else 10000
                await page.wait_for_selector(step["selector"], timeout=timeout, state="visible")

        elif action == "scroll":
            if step.get("selector"):
                element = await page.query_selector(step["selector"])
                if element:
                    await element.scroll_into_view_if_needed()
            elif step.get("value"):
                scroll_amount = int(step["value"])
                await page.evaluate(f"window.scrollBy(0, {scroll_amount})")
            await page.wait_for_timeout(300)

        elif action == "hover":
            if step.get("selector"):
                element = await self.find_element_with_fallback(page, step)
                if not element:
                    raise Exception(f"Element not found: {step['selector']}")
                await element.hover()
                await page.wait_for_timeout(300)

        elif action == "pressKey":
            if step.get("value"):
                await page.keyboard.press(step["value"])
                await page.wait_for_timeout(200)

        elif action == "extract":
            if step.get("selector"):
                return await self.extract_data(page, step)

        elif action == "extractTable":
            if step.get("selector"):
                return await self.extract_table_data(page, step["selector"])

        elif action == "verify":
            if step.get("selector"):
                element = await self.find_element_with_fallback(page, step)
                if not element:
                    raise Exception(f"Verification failed: {step['selector']} not found")
                if step.get("value"):
                    text = await element.text_content()
                    if not text or step["value"] not in text:
                        raise Exception(f"Verification failed: Expected text \"{step['value']}\" not found")

        elif action == "screenshot":
            screenshot = await page.screenshot(
                type="jpeg",
                quality=80,
                full_page=step.get("value") == "fullPage"
            )
            return {"screenshot": f"data:image/jpeg;base64,{base64.b64encode(screenshot).decode()}"}

        return None

    async def find_element_with_fallback(self, page: Page, step: dict) -> any:
        selectors = [s for s in [
            step.get("selector"),
            step.get("xpath"),
            step.get("textSelector"),
            *step.get("fallbackSelectors", [])
        ] if s]

        for selector in selectors:
            try:
                if selector.startswith("//") or selector.startswith("(//"):
                    await page.wait_for_selector(f"xpath={selector}", timeout=5000, state="visible")
                    element = await page.query_selector(f"xpath={selector}")
                    if element:
                        return element
                elif selector.startswith("text="):
                    text = selector.replace("text=", "").replace('"', '')
                    await page.wait_for_selector(f"text={text}", timeout=5000, state="visible")
                    element = await page.query_selector(f"text={text}")
                    if element:
                        return element
                else:
                    await page.wait_for_selector(selector, timeout=5000, state="visible")
                    element = await page.query_selector(selector)
                    if element:
                        return element
            except Exception as error:
                print(f"Selector failed: {selector}, trying next...")
                continue

        return None

    async def extract_data(self, page: Page, step: dict) -> dict:
        try:
            if not step.get("selector"):
                return None

            elements = await page.query_selector_all(step["selector"])
            data = []

            for element in elements:
                text = await element.text_content()
                value = await element.evaluate("el => el.value")
                attributes = await element.evaluate("""el => {
                    const attrs = {};
                    for (const attr of el.attributes) {
                        attrs[attr.name] = attr.value;
                    }
                    return attrs;
                }""")

                data.append({
                    "text": text.strip() if text else None,
                    "value": value,
                    "attributes": attributes
                })

            return {step.get("value", "extracted"): data}
        except Exception as error:
            print(f"Error extracting data: {error}")
            return None

    async def extract_table_data(self, page: Page, selector: str) -> dict:
        try:
            table_data = await page.evaluate(f"""
                (sel => {{
                    const table = document.querySelector(sel);
                    if (!table) return null;

                    const headers = [];
                    const rows = [];

                    const headerCells = table.querySelectorAll('thead th, thead td');
                    headerCells.forEach(cell => {{
                        headers.push(cell.textContent?.trim() || '');
                    }});

                    const bodyRows = table.querySelectorAll('tbody tr');
                    bodyRows.forEach(row => {{
                        const rowData = {{}};
                        const cells = row.querySelectorAll('td, th');
                        cells.forEach((cell, index) => {{
                            const header = headers[index] || `column_${{index}}`;
                            rowData[header] = cell.textContent?.trim() || '';
                        }});
                        rows.push(rowData);
                    }});

                    return {{ headers, rows }};
                }})("{selector}")
            """)

            return {"tableData": table_data}
        except Exception as error:
            print(f"Error extracting table: {error}")
            return None

    async def record_actions(self, url: str, duration: int = 60000) -> list[dict]:
        await self.initialize()
        page = await self.context.new_page()
        recorded_actions = []

        await page.goto(url)

        await page.expose_function("recordClick", lambda selector, text: recorded_actions.append({
            "action": "click",
            "selector": selector,
            "description": f"Click on \"{text or selector}\""
        }))

        await page.expose_function("recordType", lambda selector, value: recorded_actions.append({
            "action": "type",
            "selector": selector,
            "value": value,
            "description": f"Type \"{value}\" into {selector}"
        }))

        await page.evaluate("""() => {
            document.addEventListener('click', e => {
                const target = e.target;
                const selector = target.id 
                    ? `#${target.id}` 
                    : target.getAttribute('data-testid')
                    ? `[data-testid="${target.getAttribute('data-testid')}"]`
                    : target.tagName.toLowerCase();
                window.recordClick(selector, target.textContent?.trim());
            });

            document.addEventListener('input', e => {
                const target = e.target;
                const selector = target.id 
                    ? `#${target.id}` 
                    : target.getAttribute('name')
                    ? `[name="${target.getAttribute('name')}"]`
                    : 'input';
                window.recordType(selector, target.value);
            });
        }""")

        await page.wait_for_timeout(duration)
        await page.close()

        return recorded_actions

    async def get_cookies(self) -> list[dict]:
        if self.context:
            return await self.context.cookies()
        return []

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

automation_service = AutomationService()
