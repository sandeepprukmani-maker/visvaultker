"""
AI-Based Script Generation Service
Uses detailed prompts with validated locators to generate clean, error-free scripts
"""
import logging
import os
from typing import Dict, Any, Optional
from app.services.enhanced_prompt_generator import DetailedPrompt
from openai import OpenAI
from auth.oauth_handler import get_oauth_token_with_retry

logger = logging.getLogger(__name__)


class AIScriptGenerator:
    """
    Generates Python Playwright scripts using AI models
    
    Uses OAuth gateway authentication (same as browser engines)
    to generate clean, error-free Playwright scripts
    """
    
    def __init__(self, model_provider: str = "oauth_gateway"):
        """
        Initialize AI script generator
        
        Args:
            model_provider: 'oauth_gateway' (uses OAuth authentication like engines)
        """
        self.model_provider = model_provider
        self._init_client()
        
    def _init_client(self):
        """Initialize AI client using OAuth gateway authentication"""
        try:
            # Get gateway configuration (same as engines use)
            gateway_base_url = os.environ.get('GW_BASE_URL')
            if not gateway_base_url:
                logger.warning("GW_BASE_URL not set, AI generation unavailable")
                self.client = None
                return
            
            # Get OAuth token (same method as engines use)
            try:
                oauth_token = get_oauth_token_with_retry(max_retries=3)
            except Exception as e:
                logger.warning(f"Failed to obtain OAuth token: {str(e)}. AI generation unavailable.")
                self.client = None
                return
            
            # Initialize OpenAI client with gateway and OAuth token
            self.client = OpenAI(
                base_url=gateway_base_url,
                api_key=oauth_token,
                default_headers={
                    "Authorization": f"Bearer {oauth_token}"
                }
            )
            
            logger.info(f"✅ AI Script Generator initialized with OAuth gateway: {gateway_base_url}")
                
        except Exception as e:
            logger.error(f"Failed to initialize AI client: {e}")
            self.client = None
    
    def generate_script(
        self,
        detailed_prompt: DetailedPrompt,
        headless: bool = True
    ) -> Dict[str, Any]:
        """
        Generate a Python Playwright script using AI
        
        Args:
            detailed_prompt: DetailedPrompt with validated element information
            headless: Run in headless mode
            
        Returns:
            Dict with generated script and metadata
        """
        logger.info(f"🤖 Generating script using OAuth gateway AI model")
        
        if not self.client:
            logger.warning("⚠️  AI client not available, falling back to template generation")
            return self._fallback_template_generation(detailed_prompt, headless)
        
        try:
            # Build the AI prompt
            system_prompt = self._create_system_prompt()
            user_prompt = self._create_user_prompt(detailed_prompt, headless)
            
            # Get model from config (same as engines use)
            model = os.environ.get('OPENAI_MODEL', 'gpt-4o-2024-11-20')
            
            # Generate code using OAuth gateway
            code = self._generate_with_oauth_gateway(system_prompt, user_prompt, model)
            
            logger.info(f"✅ AI script generated ({len(code)} chars)")
            
            return {
                'success': True,
                'code': code,
                'model_provider': 'oauth_gateway',
                'confidence': detailed_prompt.confidence_score,
                'prompt_used': user_prompt
            }
            
        except Exception as e:
            logger.error(f"❌ AI generation failed: {e}", exc_info=True)
            return self._fallback_template_generation(detailed_prompt, headless)
    
    def _create_system_prompt(self) -> str:
        """Create system prompt for AI model"""
        return """You are an expert Python Playwright automation engineer. Your task is to generate clean, production-ready Playwright scripts.

Follow these principles:
1. Use ONLY the validated locators provided in the prompt
2. Include proper error handling with try/except blocks
3. Add appropriate waits (wait_for_load_state, wait_for_timeout)
4. Use async/await for all Playwright operations
5. Include helpful comments explaining each step
6. Add assertions to verify expected results
7. Use .first when locators might match multiple elements
8. Implement retry logic for critical operations
9. Generate syntactically correct, executable Python code
10. Follow PEP 8 style guidelines

Generate ONLY the Python code, no explanations or markdown."""
    
    def _create_user_prompt(self, detailed_prompt: DetailedPrompt, headless: bool) -> str:
        """Create user prompt with validated element information"""
        prompt_parts = []
        
        prompt_parts.append(detailed_prompt.prompt_text)
        prompt_parts.append("\n---\n")
        prompt_parts.append(f"Generate headless={'True' if headless else 'False'} mode script.")
        prompt_parts.append("Use the EXACT validated locators provided above.")
        prompt_parts.append("Include all necessary imports and proper async structure.")
        
        return "\n".join(prompt_parts)
    
    def _generate_with_oauth_gateway(self, system: str, user: str, model: str) -> str:
        """Generate code using OAuth gateway (same as browser engines)"""
        response = self.client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user}
            ],
            temperature=0.3,
            max_tokens=4096
        )
        
        code = response.choices[0].message.content
        return self._extract_code_from_response(code)
    
    def _extract_code_from_response(self, response: str) -> str:
        """Extract Python code from AI response"""
        # Remove markdown code blocks if present
        if "```python" in response:
            parts = response.split("```python")
            if len(parts) > 1:
                code = parts[1].split("```")[0]
                return code.strip()
        elif "```" in response:
            parts = response.split("```")
            if len(parts) > 1:
                code = parts[1]
                return code.strip()
        
        # Return as-is if no code blocks
        return response.strip()
    
    def _fallback_template_generation(
        self,
        detailed_prompt: DetailedPrompt,
        headless: bool
    ) -> Dict[str, Any]:
        """
        Fallback to template-based generation when AI is unavailable
        """
        logger.info("📝 Using template-based generation as fallback")
        
        code = self._generate_template_code(detailed_prompt, headless)
        
        return {
            'success': True,
            'code': code,
            'model_provider': 'template',
            'confidence': detailed_prompt.confidence_score * 0.8,  # Lower confidence for templates
            'prompt_used': detailed_prompt.prompt_text
        }
    
    def _generate_template_code(
        self,
        detailed_prompt: DetailedPrompt,
        headless: bool
    ) -> str:
        """Generate code using templates"""
        code_lines = []
        
        # Imports
        code_lines.append('"""')
        code_lines.append(f'Generated automation script for: {detailed_prompt.task_description}')
        code_lines.append('"""')
        code_lines.append('import asyncio')
        code_lines.append('from playwright.async_api import async_playwright, expect')
        code_lines.append('')
        
        # Main function
        code_lines.append('async def run_automation():')
        code_lines.append('    """Execute the automation task"""')
        code_lines.append('    async with async_playwright() as p:')
        code_lines.append(f'        browser = await p.chromium.launch(headless={headless})')
        code_lines.append('        context = await browser.new_context()')
        code_lines.append('        page = await context.new_page()')
        code_lines.append('        ')
        code_lines.append('        try:')
        
        # Generate steps
        for step in detailed_prompt.steps:
            action = step.get('action', '').lower()
            target = step.get('target', '')
            value = step.get('value', '')
            validation = step.get('validation')
            
            code_lines.append(f'            # {action.upper()}: {target}')
            
            if action == 'navigate':
                code_lines.append(f'            await page.goto("{target}", wait_until="networkidle")')
                
            elif action == 'click' and validation and validation.exists:
                code_lines.append(f'            locator = {validation.locator}')
                code_lines.append('            await expect(locator).to_be_visible()')
                code_lines.append('            await locator.click()')
                
            elif action == 'fill' and validation and validation.exists:
                code_lines.append(f'            locator = {validation.locator}')
                code_lines.append('            await expect(locator).to_be_visible()')
                code_lines.append(f'            await locator.fill("{value}")')
                
            elif action == 'verify' and validation and validation.exists:
                code_lines.append(f'            await expect({validation.locator}).to_be_visible()')
                
            elif action == 'wait':
                ms = 2000  # default
                code_lines.append(f'            await page.wait_for_timeout({ms})')
            
            code_lines.append('            ')
        
        # Cleanup
        code_lines.append('            print("✅ Automation completed successfully")')
        code_lines.append('            ')
        code_lines.append('        except Exception as e:')
        code_lines.append('            print(f"❌ Error: {e}")')
        code_lines.append('            await page.screenshot(path="error.png")')
        code_lines.append('            raise')
        code_lines.append('        finally:')
        code_lines.append('            await browser.close()')
        code_lines.append('')
        code_lines.append('')
        code_lines.append('if __name__ == "__main__":')
        code_lines.append('    asyncio.run(run_automation())')
        
        return '\n'.join(code_lines)


def generate_script_from_prompt(
    detailed_prompt: DetailedPrompt,
    headless: bool = True,
    model_provider: str = "anthropic"
) -> Dict[str, Any]:
    """
    Convenience function to generate script from detailed prompt
    
    Args:
        detailed_prompt: DetailedPrompt with validated information
        headless: Run in headless mode
        model_provider: AI provider ('anthropic', 'openai', 'groq')
        
    Returns:
        Dict with generated code and metadata
    """
    generator = AIScriptGenerator(model_provider)
    return generator.generate_script(detailed_prompt, headless)
