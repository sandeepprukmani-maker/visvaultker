"""
Browser-Use Code Generator
Converts browser-use execution history into rerunnable Python Playwright scripts
"""
import logging
import re
import hashlib
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class BrowserUseCodeGenerator:
    """
    Generates production-ready Python Playwright code from browser-use execution history
    Uses LLM to intelligently extract locators and actions from natural language steps
    """
    
    def __init__(self, llm_client):
        """
        Initialize code generator
        
        Args:
            llm_client: LLM client for intelligent code generation
        """
        self.llm_client = llm_client
        logger.info("🎨 Browser-Use Code Generator initialized")
    
    def generate_script(
        self,
        instruction: str,
        steps: List[Dict],
        final_result: Optional[str] = None,
        start_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate Python Playwright script from browser-use execution history
        
        Args:
            instruction: Original user instruction
            steps: List of executed steps from browser-use
            final_result: Final result message from execution
            start_url: Starting URL (extracted from steps if not provided)
            
        Returns:
            Dictionary containing python_code, script_hash, and metadata
        """
        try:
            logger.info(f"🎨 Generating Python script for: '{instruction}'")
            
            if not steps or len(steps) == 0:
                logger.warning("⚠️  No steps to generate code from")
                return {
                    'python_code': self._generate_empty_script(instruction),
                    'script_hash': '',
                    'metadata': {'error': 'No steps executed'}
                }
            
            # Extract start URL from steps if not provided
            if not start_url:
                start_url = self._extract_start_url(steps)
            
            # Generate code using LLM
            python_code = self._generate_with_llm(
                instruction=instruction,
                steps=steps,
                final_result=final_result,
                start_url=start_url
            )
            
            # Calculate script hash for versioning
            script_hash = hashlib.sha256(python_code.encode()).hexdigest()
            
            logger.info("✅ Python script generated successfully")
            
            return {
                'python_code': python_code,
                'script_hash': script_hash,
                'metadata': {
                    'instruction': instruction,
                    'steps_count': len(steps),
                    'start_url': start_url,
                    'generated_at': datetime.utcnow().isoformat(),
                    'lines_of_code': len(python_code.split('\n'))
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Code generation failed: {e}", exc_info=True)
            # Return fallback script
            return {
                'python_code': self._generate_fallback_script(instruction, steps),
                'script_hash': '',
                'metadata': {'error': str(e), 'fallback': True}
            }
    
    def _extract_start_url(self, steps: List[Dict]) -> str:
        """Extract starting URL from execution steps"""
        for step in steps[:5]:  # Check first 5 steps
            action = step.get('arguments', {}).get('action', '').lower()
            
            # Look for URL patterns
            url_patterns = [
                r'https?://[^\s]+',
                r'www\.[^\s]+',
                r'go to ([^\s]+)',
                r'navigate to ([^\s]+)',
                r'open ([^\s]+)'
            ]
            
            for pattern in url_patterns:
                match = re.search(pattern, action)
                if match:
                    url = match.group(1) if match.lastindex else match.group(0)
                    # Clean up URL
                    url = url.strip('.,;:)\'"')
                    if not url.startswith('http'):
                        url = f'https://{url}'
                    logger.info(f"📍 Extracted start URL: {url}")
                    return url
        
        logger.warning("⚠️  Could not extract start URL, using placeholder")
        return 'https://example.com'
    
    def _generate_with_llm(
        self,
        instruction: str,
        steps: List[Dict],
        final_result: Optional[str],
        start_url: str
    ) -> str:
        """Generate Python code using LLM with intelligent locator extraction"""
        
        # Prepare step descriptions for LLM
        step_descriptions = []
        for i, step in enumerate(steps, 1):
            action = step.get('arguments', {}).get('action', '')
            step_descriptions.append(f"{i}. {action}")
        
        steps_text = "\n".join(step_descriptions)
        
        prompt = f"""Convert this browser automation task into a production-ready Python Playwright script.

**Original Task:** {instruction}

**Starting URL:** {start_url}

**Executed Steps:**
{steps_text}

**Requirements:**
1. Generate complete, standalone Python script using async Playwright
2. Use STRICT locators following this priority:
   - get_by_role() with name for buttons, links, inputs (highest priority)
   - get_by_placeholder() for input fields with placeholders
   - get_by_label() for form inputs with labels
   - get_by_text() for text-based elements
   - locator() with CSS/data-testid only as last resort
3. Include proper error handling with try/except
4. Add retry logic for flaky operations (3 attempts)
5. Include detailed logging for debugging
6. Add timeouts (30s default)
7. Use async/await patterns throughout
8. Make code reusable and maintainable

**Template Structure:**
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
    \"\"\"
    {instruction}
    \"\"\"
    async with async_playwright() as p:
        logger.info("Launching browser...")
        browser = await p.chromium.launch(headless=False)
        
        try:
            context = await browser.new_context(
                viewport={{'width': 1280, 'height': 720}}
            )
            page = await context.new_page()
            page.set_default_timeout(30000)
            
            logger.info("Starting automation...")
            
            # Step 1: Navigate to starting URL
            logger.info(f"Navigating to {{start_url}}")
            await page.goto('{start_url}')
            await page.wait_for_load_state('networkidle')
            
            # [GENERATE STEPS HERE - Convert each action into proper Playwright code]
            # Example:
            # logger.info("Step 2: Click login button")
            # await retry_async(lambda: page.get_by_role('button', name='Login').click())
            
            logger.info("✅ Automation completed successfully")
            
        except PlaywrightTimeout as e:
            logger.error(f"❌ Timeout error: {{e}}")
            raise
        except Exception as e:
            logger.error(f"❌ Automation failed: {{e}}")
            raise
        finally:
            await browser.close()
            logger.info("Browser closed")


if __name__ == "__main__":
    asyncio.run(main())
```

**Critical Instructions:**
- Analyze each step and determine the most appropriate Playwright locator
- Use get_by_role() whenever possible for accessibility and reliability
- Include retry logic for click/fill operations
- Add meaningful log messages for each step
- Make the code production-ready and executable
- Return ONLY the complete Python code, no explanations

Generate the complete script now:"""
        
        try:
            # LangChain ChatOpenAI uses invoke() method, not chat.completions.create()
            from langchain_core.messages import SystemMessage, HumanMessage
            
            messages = [
                SystemMessage(content="You are an expert at converting browser automation workflows into production-ready Python Playwright code with strict, reliable locators. Always use best practices for locator selection and error handling."),
                HumanMessage(content=prompt)
            ]
            
            response = self.llm_client.invoke(messages)
            
            # LangChain returns AIMessage with content attribute
            code_text = response.content if hasattr(response, 'content') else str(response)
            code = self._extract_python_code_from_text(code_text)
            return code
            
        except Exception as e:
            logger.error(f"❌ LLM code generation failed: {e}", exc_info=True)
            logger.warning("⚠️  Falling back to template-based code generation")
            return self._generate_fallback_script(instruction, steps)
    
    def _extract_python_code_from_text(self, text: str) -> str:
        """Extract Python code from LLM response text"""
        if not text:
            return ""
        
        # Look for Python code blocks
        python_pattern = r'```python\s*\n(.*?)\n```'
        matches = re.findall(python_pattern, text, re.DOTALL)
        
        if matches:
            return matches[0].strip()
        
        # If no code block, try to extract code directly
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
        
        # Fallback: return entire text
        return text.strip()
    
    def _generate_empty_script(self, instruction: str) -> str:
        """Generate empty script template when no steps available"""
        return f'''"""
Generated Playwright Script - No Steps Executed
Task: {instruction}
"""
import asyncio
import logging
from playwright.async_api import async_playwright

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    """
    {instruction}
    
    NOTE: No automation steps were executed. This is a template.
    """
    async with async_playwright() as p:
        logger.info("Launching browser...")
        browser = await p.chromium.launch(headless=False)
        
        try:
            context = await browser.new_context()
            page = await context.new_page()
            
            logger.info("TODO: Add automation steps here")
            # Add your automation steps
            
            logger.info("Automation template ready")
            
        finally:
            await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
'''
    
    def _generate_fallback_script(self, instruction: str, steps: List[Dict]) -> str:
        """Generate fallback script when LLM fails"""
        step_comments = []
        for i, step in enumerate(steps, 1):
            action = step.get('arguments', {}).get('action', 'Unknown action')
            step_comments.append(f"    # Step {i}: {action}")
        
        steps_text = '\n'.join(step_comments)
        
        return f'''"""
Generated Playwright Script (Fallback)
Task: {instruction}
"""
import asyncio
import logging
from playwright.async_api import async_playwright

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    """
    {instruction}
    """
    async with async_playwright() as p:
        logger.info("Launching browser...")
        browser = await p.chromium.launch(headless=False)
        
        try:
            context = await browser.new_context()
            page = await context.new_page()
            
            logger.info("Starting automation...")
            
{steps_text}
            # TODO: Convert the above steps into Playwright code
            
            logger.info("Automation steps completed")
            
        finally:
            await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
'''
