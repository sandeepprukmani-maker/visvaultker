"""
Dynamic Healing Agent
Automatically handles and resolves execution issues in real-time
"""
import logging
import re
from typing import Dict, Any, Optional, List
from app.services.intelligent_validator import IntelligentValidator
from app.services.ai_script_generator import AIScriptGenerator
from app.services.enhanced_prompt_generator import EnhancedPromptGenerator, DetailedPrompt

logger = logging.getLogger(__name__)


class DynamicHealerAgent:
    """
    Enhanced healing agent that dynamically resolves execution issues
    
    Features:
    - Real-time error detection and resolution
    - Re-validation of failed elements
    - AI-powered script regeneration
    - Adaptive healing strategies
    - Context-aware fixes
    """
    
    def __init__(self, model_provider: str = "anthropic"):
        """
        Initialize dynamic healer
        
        Args:
            model_provider: AI provider for regeneration
        """
        self.validator = IntelligentValidator()
        self.prompt_generator = EnhancedPromptGenerator()
        self.script_generator = AIScriptGenerator(model_provider)
        self.healing_history = []
        
    async def heal_dynamically(
        self,
        original_script: str,
        error_message: str,
        execution_logs: str,
        task_description: str,
        url: str,
        headless: bool = True
    ) -> Dict[str, Any]:
        """
        Dynamically heal a failed script by re-validating and regenerating
        
        Args:
            original_script: The failing script
            error_message: Error that occurred
            execution_logs: Logs from execution
            task_description: Original task description
            url: Target URL
            headless: Run headless
            
        Returns:
            Dict with healed script and healing metadata
        """
        logger.info("🩺 Dynamic healing initiated")
        
        try:
            # Analyze the error
            error_analysis = self._analyze_error(error_message, execution_logs)
            logger.info(f"   Error type: {error_analysis['type']}")
            logger.info(f"   Root cause: {error_analysis['root_cause']}")
            
            # Determine healing strategy
            strategy = self._select_healing_strategy(error_analysis)
            logger.info(f"   Healing strategy: {strategy}")
            
            # Apply the healing strategy
            if strategy == 'revalidate_and_regenerate':
                healed = await self._revalidate_and_regenerate(
                    task_description, url, error_analysis, headless
                )
            elif strategy == 'pattern_based_fix':
                healed = await self._apply_pattern_fixes(
                    original_script, error_analysis
                )
            elif strategy == 'ai_assisted_fix':
                healed = await self._ai_assisted_fix(
                    original_script, error_analysis, task_description
                )
            else:
                # Fallback to basic fixes
                healed = await self._apply_basic_fixes(original_script, error_analysis)
            
            # Record healing history
            self.healing_history.append({
                'error_type': error_analysis['type'],
                'strategy': strategy,
                'success': healed.get('success', False)
            })
            
            logger.info(f"✅ Dynamic healing complete (strategy: {strategy})")
            
            return healed
            
        except Exception as e:
            logger.error(f"❌ Dynamic healing failed: {e}", exc_info=True)
            return {
                'success': False,
                'healed_script': original_script,
                'error': str(e),
                'strategy': 'none'
            }
    
    def _analyze_error(
        self,
        error_message: str,
        execution_logs: str
    ) -> Dict[str, Any]:
        """Analyze error to determine root cause and best healing approach"""
        combined = f"{error_message}\n{execution_logs}".lower()
        
        analysis = {
            'type': 'unknown',
            'root_cause': '',
            'severity': 'medium',
            'is_recoverable': True,
            'failing_element': None,
            'suggested_actions': []
        }
        
        # Detect error types
        if any(pattern in combined for pattern in ['locator', 'selector', 'element', 'not found']):
            analysis['type'] = 'locator_error'
            analysis['root_cause'] = 'Element locator failed to find target'
            analysis['severity'] = 'high'
            analysis['suggested_actions'] = [
                'Revalidate element existence',
                'Try alternative locators',
                'Check if element is dynamically loaded'
            ]
            
            # Extract failing locator
            locator_match = re.search(r'locator\([\'"]([^\'"]+)[\'"]\)', error_message)
            if locator_match:
                analysis['failing_element'] = locator_match.group(1)
        
        elif any(pattern in combined for pattern in ['timeout', 'timed out', 'deadline']):
            analysis['type'] = 'timeout_error'
            analysis['root_cause'] = 'Operation exceeded timeout limit'
            analysis['severity'] = 'medium'
            analysis['suggested_actions'] = [
                'Increase timeout values',
                'Add explicit waits',
                'Check network conditions'
            ]
        
        elif any(pattern in combined for pattern in ['not visible', 'not clickable', 'hidden']):
            analysis['type'] = 'visibility_error'
            analysis['root_cause'] = 'Element not in visible/clickable state'
            analysis['severity'] = 'medium'
            analysis['suggested_actions'] = [
                'Scroll element into view',
                'Wait for element to be visible',
                'Check for overlays or modals'
            ]
        
        elif any(pattern in combined for pattern in ['syntax', 'invalid syntax', 'indentation']):
            analysis['type'] = 'syntax_error'
            analysis['root_cause'] = 'Python syntax error in generated code'
            analysis['severity'] = 'critical'
            analysis['is_recoverable'] = True
            analysis['suggested_actions'] = [
                'Regenerate script with AI',
                'Fix indentation',
                'Validate Python syntax'
            ]
        
        elif any(pattern in combined for pattern in ['network', 'connection', 'dns']):
            analysis['type'] = 'network_error'
            analysis['root_cause'] = 'Network connectivity issue'
            analysis['severity'] = 'high'
            analysis['suggested_actions'] = [
                'Add retry logic',
                'Check URL accessibility',
                'Increase navigation timeout'
            ]
        
        return analysis
    
    def _select_healing_strategy(self, error_analysis: Dict[str, Any]) -> str:
        """Select the best healing strategy based on error analysis"""
        error_type = error_analysis['type']
        severity = error_analysis['severity']
        
        # High-severity errors need full regeneration
        if error_type == 'locator_error' and severity == 'high':
            return 'revalidate_and_regenerate'
        
        # Syntax errors need AI assistance
        elif error_type == 'syntax_error':
            return 'ai_assisted_fix'
        
        # Timing issues can use pattern fixes
        elif error_type in ['timeout_error', 'visibility_error']:
            return 'pattern_based_fix'
        
        # Network errors need retries
        elif error_type == 'network_error':
            return 'pattern_based_fix'
        
        # Unknown errors try pattern fixes first
        else:
            return 'pattern_based_fix'
    
    async def _revalidate_and_regenerate(
        self,
        task_description: str,
        url: str,
        error_analysis: Dict[str, Any],
        headless: bool
    ) -> Dict[str, Any]:
        """
        Revalidate elements and regenerate script
        
        This is the most thorough healing approach
        """
        logger.info("   🔄 Revalidating and regenerating script...")
        
        try:
            # Extract steps from task description (simplified)
            # In production, this would use the original plan
            steps = self._extract_steps_from_description(task_description)
            
            # Generate new detailed prompt with validation
            detailed_prompt = await self.prompt_generator.generate_detailed_prompt(
                task_description, url, steps, headless
            )
            
            # Regenerate script using AI
            result = self.script_generator.generate_script(detailed_prompt, headless)
            
            if result.get('success'):
                return {
                    'success': True,
                    'healed_script': result['code'],
                    'strategy': 'revalidate_and_regenerate',
                    'confidence': detailed_prompt.confidence_score,
                    'healing_notes': 'Script regenerated with revalidated elements'
                }
            else:
                raise Exception("Script generation failed")
                
        except Exception as e:
            logger.error(f"Revalidation failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'strategy': 'revalidate_and_regenerate'
            }
    
    async def _apply_pattern_fixes(
        self,
        script: str,
        error_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply pattern-based fixes to the script"""
        logger.info("   🔧 Applying pattern-based fixes...")
        
        healed = script
        error_type = error_analysis['type']
        
        if error_type == 'timeout_error':
            # Increase timeouts
            healed = re.sub(r'timeout=(\d+)', 
                          lambda m: f'timeout={int(m.group(1)) * 2}', 
                          healed)
            
            # Add networkidle waits
            healed = re.sub(r'page\.goto\("([^"]+)"\)',
                          r'page.goto("\1", wait_until="networkidle", timeout=60000)',
                          healed)
        
        elif error_type == 'visibility_error':
            # Add scroll into view
            healed = healed.replace(
                '.click()',
                '.scroll_into_view_if_needed()\n            await page.wait_for_timeout(500)\n            .click()'
            )
            
            # Add visibility checks
            healed = re.sub(r'(await locator\.click\(\))',
                          r'await expect(locator).to_be_visible()\n            \1',
                          healed)
        
        elif error_type == 'network_error':
            # Add retry logic
            healed = self._add_retry_wrapper(healed)
        
        return {
            'success': True,
            'healed_script': healed,
            'strategy': 'pattern_based_fix',
            'healing_notes': f'Applied {error_type} fixes'
        }
    
    async def _ai_assisted_fix(
        self,
        script: str,
        error_analysis: Dict[str, Any],
        task_description: str
    ) -> Dict[str, Any]:
        """Use AI to fix the script"""
        logger.info("   🤖 Using AI to fix script...")
        
        try:
            if not self.script_generator.client:
                raise Exception("AI client not available")
            
            fix_prompt = self._create_fix_prompt(script, error_analysis, task_description)
            
            # Use AI to fix the script
            if self.script_generator.model_provider == "anthropic":
                fixed = await self._fix_with_anthropic(fix_prompt)
            else:
                # Fallback to pattern fixes
                return await self._apply_pattern_fixes(script, error_analysis)
            
            return {
                'success': True,
                'healed_script': fixed,
                'strategy': 'ai_assisted_fix',
                'healing_notes': 'Script fixed using AI assistance'
            }
            
        except Exception as e:
            logger.error(f"AI fix failed: {e}")
            return await self._apply_pattern_fixes(script, error_analysis)
    
    async def _apply_basic_fixes(
        self,
        script: str,
        error_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply basic, safe fixes"""
        logger.info("   ⚙️  Applying basic fixes...")
        
        healed = script
        
        # Add general error resilience
        if 'try:' not in healed:
            healed = self._wrap_in_try_except(healed)
        
        # Add general waits
        healed = healed.replace(
            'await page.goto',
            'await page.wait_for_timeout(1000)\n        await page.goto'
        )
        
        return {
            'success': True,
            'healed_script': healed,
            'strategy': 'basic_fixes',
            'healing_notes': 'Applied basic resilience improvements'
        }
    
    def _extract_steps_from_description(self, description: str) -> List[Dict[str, Any]]:
        """Extract basic steps from task description (simplified)"""
        # This is a simplified version
        # In production, you'd use the original plan
        return [
            {
                'action': 'navigate',
                'target': 'URL from description',
                'value': ''
            }
        ]
    
    def _create_fix_prompt(
        self,
        script: str,
        error_analysis: Dict[str, Any],
        task_description: str
    ) -> str:
        """Create prompt for AI to fix the script"""
        return f"""Fix the following Python Playwright script that has an error.

Task: {task_description}

Error Type: {error_analysis['type']}
Root Cause: {error_analysis['root_cause']}
Suggested Actions:
{chr(10).join(f'- {action}' for action in error_analysis['suggested_actions'])}

Original Script:
```python
{script}
```

Generate a fixed version of the script that resolves the error.
Return ONLY the Python code, no explanations."""
    
    async def _fix_with_anthropic(self, prompt: str) -> str:
        """Fix script using Anthropic Claude"""
        response = self.script_generator.client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=4096,
            temperature=0.2,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        code = response.content[0].text
        return self.script_generator._extract_code_from_response(code)
    
    def _add_retry_wrapper(self, script: str) -> str:
        """Add retry logic to navigation"""
        # Add retry to page.goto
        script = re.sub(
            r'await page\.goto\("([^"]+)"[^)]*\)',
            r'''for attempt in range(3):
                try:
                    await page.goto("\1", wait_until="networkidle", timeout=60000)
                    break
                except Exception as e:
                    if attempt == 2:
                        raise
                    await page.wait_for_timeout(2000)''',
            script
        )
        return script
    
    def _wrap_in_try_except(self, script: str) -> str:
        """Wrap script execution in try/except"""
        # Simplified implementation
        return script
    
    def heal_sync(
        self,
        original_script: str,
        error_message: str,
        execution_logs: str,
        task_description: str,
        url: str,
        headless: bool = True
    ) -> Dict[str, Any]:
        """Synchronous version of heal_dynamically"""
        import asyncio
        return asyncio.run(
            self.heal_dynamically(
                original_script,
                error_message,
                execution_logs,
                task_description,
                url,
                headless
            )
        )
