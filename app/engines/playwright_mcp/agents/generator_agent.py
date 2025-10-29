"""
Generator Agent
Converts automation plans into production-ready standalone Python Playwright scripts
"""
import logging
import yaml
import json
import hashlib
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class GeneratorAgent:
    """
    Generator Agent that transforms YAML automation plans into executable Python Playwright code
    Generates production-ready scripts with async/await, error handling, retry logic, and logging
    """
    
    def __init__(self, llm_client, locator_engine):
        """
        Initialize Generator Agent
        
        Args:
            llm_client: LLM client for code generation
            locator_engine: StrictModeLocatorEngine instance
        """
        self.llm_client = llm_client
        self.locator_engine = locator_engine
    
    def generate_script(self, plan_yaml: str, progress_callback=None) -> Dict[str, Any]:
        """
        Generate Python Playwright script from automation plan
        
        Args:
            plan_yaml: YAML automation plan
            progress_callback: Optional callback for progress updates
            
        Returns:
            Dictionary containing python_code, script_hash, and metadata
        """
        try:
            if progress_callback:
                progress_callback('generator_init', {
                    'message': '🎨 Generator Agent: Parsing automation plan...'
                })
            
            # Parse the YAML plan
            plan = yaml.safe_load(plan_yaml)
            
            logger.info(f"🎨 Generator Agent: Generating Python script for '{plan.get('goal', 'Unknown')}'")
            
            if progress_callback:
                progress_callback('generator_building', {
                    'message': '🎨 Generator Agent: Building production-ready Python code...'
                })
            
            # Generate the Python code using LLM
            python_code = self._generate_with_llm(plan)
            
            # Calculate script hash for versioning
            script_hash = hashlib.sha256(python_code.encode()).hexdigest()
            
            if progress_callback:
                progress_callback('generator_complete', {
                    'message': '🎨 Generator Agent: Python script generated successfully!',
                    'lines': len(python_code.split('\n'))
                })
            
            logger.info("✅ Generator Agent: Successfully generated Python Playwright script")
            
            return {
                'python_code': python_code,
                'script_hash': script_hash,
                'metadata': json.dumps({
                    'lines_of_code': len(python_code.split('\n')),
                    'plan_steps': len(plan.get('steps', [])),
                    'generated_at': datetime.utcnow().isoformat()
                })
            }
            
        except Exception as e:
            logger.error(f"❌ Generator Agent error: {e}", exc_info=True)
            raise
    
    def _generate_with_llm(self, plan: Dict) -> str:
        """Generate Python code using LLM"""
        
        prompt = self._build_generation_prompt(plan)
        
        response = self.llm_client.chat.completions.create(
            model="gpt-4o",
            max_tokens=8192,
            temperature=0.1,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )
        
        # Extract code from response
        code = self._extract_python_code(response)
        
        return code
    
    def _build_generation_prompt(self, plan: Dict) -> str:
        """Build prompt for code generation"""
        plan_yaml = yaml.dump(plan, default_flow_style=False)
        
        return f"""Generate a standalone, production-ready Python Playwright script from this automation plan:

```yaml
{plan_yaml}
```

**Requirements**:
1. **Async/Await**: Use proper async/await patterns with asyncio
2. **Error Handling**: Wrap actions in try/except with specific error handling
3. **Retry Logic**: Add automatic retry for flaky operations (max 3 retries)
4. **Context Managers**: Use proper browser/page lifecycle management
5. **Logging**: Add comprehensive logging for debugging
6. **Timeouts**: Set reasonable timeouts for all operations
7. **Strict Mode**: Use strict=True for locators when appropriate
8. **Comments**: Add clear comments explaining each step

**Template Structure**:
```python
import asyncio
import logging
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def retry_async(func, max_retries=3, delay=1.0):
    \"\"\"Retry helper for flaky operations\"\"\"
    for attempt in range(max_retries):
        try:
            return await func()
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            logger.warning(f"Attempt {{attempt + 1}} failed: {{e}}, retrying...")
            await asyncio.sleep(delay)


async def main():
    \"\"\"Main automation function\"\"\"
    async with async_playwright() as p:
        # Launch browser
        logger.info("Launching browser...")
        browser = await p.chromium.launch(headless=False)
        
        try:
            # Create context with viewport
            context = await browser.new_context(
                viewport={{'width': 1280, 'height': 720}}
            )
            page = await context.new_page()
            
            # Set default timeout
            page.set_default_timeout(30000)
            
            # Execute automation steps
            logger.info("Starting automation...")
            
            # [GENERATED STEPS GO HERE]
            
            logger.info("✅ Automation completed successfully")
            
        except PlaywrightTimeout as e:
            logger.error(f"❌ Timeout error: {{e}}")
            raise
        except Exception as e:
            logger.error(f"❌ Automation failed: {{e}}")
            raise
        finally:
            # Cleanup
            await browser.close()
            logger.info("Browser closed")


if __name__ == "__main__":
    asyncio.run(main())
```

**Action Handlers** (use these as needed):

**Navigate**:
```python
await page.goto("{plan.get('start_url', '')}", wait_until="networkidle")
logger.info(f"Navigated to {{page.url}}")
```

**Click**:
```python
await retry_async(lambda: page.get_by_role("button", name="Submit").click())
logger.info("Clicked Submit button")
```

**Fill Input**:
```python
await page.get_by_placeholder("Email").fill("user@example.com")
logger.info("Filled email field")
```

**Select Dropdown**:
```python
await page.select_option("select#country", value="US")
logger.info("Selected country: US")
```

**Wait for Element**:
```python
await page.wait_for_selector(".success-message", state="visible", timeout=10000)
logger.info("Success message appeared")
```

**Extract Text**:
```python
text = await page.locator(".result").inner_text()
logger.info(f"Extracted text: {{text}}")
```

**Handle Popup/Alert**:
```python
page.on("dialog", lambda dialog: asyncio.ensure_future(dialog.accept()))
```

**Switch to iframe**:
```python
frame = page.frame_locator("iframe[name='payment']")
await frame.get_by_label("Card Number").fill("4242424242424242")
```

**File Upload**:
```python
await page.set_input_files("input[type='file']", "path/to/file.pdf")
```

**Screenshot**:
```python
await page.screenshot(path="screenshot.png", full_page=True)
logger.info("Screenshot saved")
```

Generate the complete, runnable Python script. Include ALL necessary imports, error handling, and logging.
The script should be ready to save as a .py file and execute directly."""
    
    def _extract_python_code(self, response) -> str:
        """Extract Python code from LLM response"""
        import re
        
        # Get text content from OpenAI response
        text = response.choices[0].message.content if response.choices[0].message.content else ""
        
        # Look for Python code blocks
        python_pattern = r'```python\s*\n(.*?)\n```'
        matches = re.findall(python_pattern, text, re.DOTALL)
        
        if matches:
            return matches[0].strip()
        
        # If no code block found, try to extract code directly
        # Look for lines that start with import or async def
        lines = text.split('\n')
        code_started = False
        code_lines = []
        
        for line in lines:
            if line.startswith(('import ', 'from ', 'async def', 'def ', '#')):
                code_started = True
            if code_started:
                code_lines.append(line)
        
        if code_lines:
            return '\n'.join(code_lines).strip()
        
        # Fallback: return the entire text
        return text.strip()
    
    def generate_action_handler_code(self, action: str, element_data: Dict, value: Optional[str] = None) -> str:
        """
        Generate Python code for a specific action
        
        Args:
            action: Action type (click, fill, select, etc.)
            element_data: Element information from plan
            value: Optional value for fill/select actions
            
        Returns:
            Python code string for the action
        """
        locator = element_data.get('locator', 'page.locator("body")')
        
        handlers = {
            'click': f'await retry_async(lambda: {locator}.click())',
            'fill': f'await {locator}.fill("{value or ""}")',
            'press': f'await {locator}.press("{value or "Enter"}")',
            'select': f'await {locator}.select_option(value="{value or ""}")',
            'check': f'await {locator}.check()',
            'uncheck': f'await {locator}.uncheck()',
            'hover': f'await {locator}.hover()',
            'double_click': f'await retry_async(lambda: {locator}.dblclick())',
            'right_click': f'await {locator}.click(button="right")',
            'extract_text': f'text = await {locator}.inner_text()',
            'extract_value': f'value = await {locator}.input_value()',
            'wait_visible': f'await {locator}.wait_for(state="visible")',
            'wait_hidden': f'await {locator}.wait_for(state="hidden")',
        }
        
        return handlers.get(action, f'# Unknown action: {action}')
