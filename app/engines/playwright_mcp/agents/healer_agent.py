"""
Healer Agent
Analyzes Playwright trace files and automatically patches failing Python scripts
"""
import logging
import json
import re
import hashlib
from typing import Dict, Any, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)


class HealerAgent:
    """
    Healer Agent that analyzes trace files from failed executions
    and automatically patches Python Playwright scripts with fixes
    """
    
    def __init__(self, llm_client, temperature=0.7):
        """
        Initialize Healer Agent
        
        Args:
            llm_client: LLM client for intelligent healing
            temperature: LLM temperature for flexibility (default 0.7)
        """
        self.llm_client = llm_client
        self.temperature = temperature
    
    def heal_script(
        self,
        python_code: str,
        error_message: str,
        trace_path: Optional[str] = None,
        max_iterations: int = 3,
        progress_callback=None
    ) -> Dict[str, Any]:
        """
        Heal a failing Python script by analyzing errors and applying fixes
        
        Args:
            python_code: Original failing Python code
            error_message: Error message from failed execution
            trace_path: Optional path to Playwright trace file
            max_iterations: Maximum healing iterations
            progress_callback: Optional callback for progress updates
            
        Returns:
            Dictionary containing healed_code, healing_iterations, and fixes_applied
        """
        try:
            if progress_callback:
                progress_callback('healer_init', {
                    'message': '🔧 Healer Agent: Analyzing failure...',
                    'error': error_message[:200]
                })
            
            logger.info(f"🔧 Healer Agent: Starting script healing (max {max_iterations} iterations)")
            
            current_code = python_code
            healing_iteration = 0
            fixes_applied = []
            
            while healing_iteration < max_iterations:
                healing_iteration += 1
                
                if progress_callback:
                    progress_callback('healer_analyzing', {
                        'message': f'🔧 Healer Agent: Iteration {healing_iteration}/{max_iterations}...',
                        'iteration': healing_iteration
                    })
                
                logger.info(f"🔧 Healing iteration {healing_iteration}/{max_iterations}")
                
                # Analyze the error and generate a fix
                analysis = self._analyze_error(current_code, error_message, trace_path)
                
                if not analysis.get('fixable', False):
                    logger.warning("⚠️ Healer: Error appears to be unfixable")
                    if progress_callback:
                        progress_callback('healer_unfixable', {
                            'message': '⚠️ Healer: Cannot automatically fix this error',
                            'reason': analysis.get('reason', 'Unknown')
                        })
                    break
                
                # Apply the fix
                healed_code = self._apply_fix(current_code, analysis)
                
                if healed_code == current_code:
                    logger.warning("⚠️ Healer: No changes made, stopping")
                    break
                
                fix_description = analysis.get('fix_description', 'Unknown fix')
                fixes_applied.append({
                    'iteration': healing_iteration,
                    'type': analysis.get('error_type', 'unknown'),
                    'description': fix_description
                })
                
                logger.info(f"✅ Applied fix: {fix_description}")
                
                current_code = healed_code
                
                # In a real implementation, we would re-run the script here
                # For now, we'll stop after one successful fix
                break
            
            script_hash = hashlib.sha256(current_code.encode()).hexdigest()
            
            if progress_callback:
                progress_callback('healer_complete', {
                    'message': f'🔧 Healer Agent: Healing complete ({len(fixes_applied)} fixes applied)',
                    'fixes': len(fixes_applied)
                })
            
            logger.info(f"✅ Healer Agent: Completed with {len(fixes_applied)} fixes")
            
            return {
                'healed_code': current_code,
                'script_hash': script_hash,
                'healing_iterations': healing_iteration,
                'fixes_applied': json.dumps(fixes_applied),
                'success': len(fixes_applied) > 0
            }
            
        except Exception as e:
            logger.error(f"❌ Healer Agent error: {e}", exc_info=True)
            raise
    
    def _analyze_error(
        self,
        code: str,
        error_message: str,
        trace_path: Optional[str]
    ) -> Dict[str, Any]:
        """
        Analyze error and determine if it's fixable
        
        Returns:
            Dictionary with error analysis and fix strategy
        """
        
        # Quick pattern-based fixes for common errors
        common_fixes = self._check_common_errors(error_message)
        if common_fixes:
            return common_fixes
        
        # Use LLM for complex error analysis
        return self._analyze_with_llm(code, error_message, trace_path)
    
    def _check_common_errors(self, error_message: str) -> Optional[Dict[str, Any]]:
        """Check for common, easily fixable errors"""
        
        # Timeout errors
        if 'timeout' in error_message.lower() or 'timed out' in error_message.lower():
            return {
                'fixable': True,
                'error_type': 'timeout',
                'fix_description': 'Increase timeout duration',
                'fix_strategy': 'increase_timeout'
            }
        
        # Locator not found errors
        if 'locator' in error_message.lower() and ('not found' in error_message.lower() or 'no element' in error_message.lower()):
            return {
                'fixable': True,
                'error_type': 'locator_not_found',
                'fix_description': 'Update locator strategy',
                'fix_strategy': 'fix_locator'
            }
        
        # Element not visible/attached
        if 'not visible' in error_message.lower() or 'not attached' in error_message.lower():
            return {
                'fixable': True,
                'error_type': 'element_state',
                'fix_description': 'Add wait for element visibility',
                'fix_strategy': 'wait_for_visible'
            }
        
        # Multiple elements matched
        if 'strict mode violation' in error_message.lower() or 'multiple elements' in error_message.lower():
            return {
                'fixable': True,
                'error_type': 'multiple_matches',
                'fix_description': 'Add .first() or .nth() to locator',
                'fix_strategy': 'strict_mode_fix'
            }
        
        return None
    
    def _analyze_with_llm(
        self,
        code: str,
        error_message: str,
        trace_path: Optional[str]
    ) -> Dict[str, Any]:
        """Use LLM to analyze complex errors"""
        
        prompt = f"""Analyze Playwright error:

Script:
```python
{code}
```

Error:
```
{error_message}
```

{f"Trace: {trace_path}" if trace_path else ""}

JSON response:
{{"fixable": bool, "error_type": "timeout|locator|network|state", "fix_description": "...", "fix_strategy": "increase_timeout|fix_locator|add_wait|strict_mode", "reason": "..."}}"""
        
        response = self.llm_client.chat.completions.create(
            model="gpt-4o",
            max_tokens=1024,
            temperature=self.temperature,
            messages=[{"role": "user", "content": prompt}]
        )
        
        # Extract JSON from response
        text = response.choices[0].message.content if response.choices[0].message.content else ""
        
        try:
            # Extract JSON from code blocks or directly
            json_pattern = r'```json\s*\n(.*?)\n```'
            matches = re.findall(json_pattern, text, re.DOTALL)
            
            if matches:
                return json.loads(matches[0])
            else:
                return json.loads(text)
        except Exception as e:
            logger.error(f"Failed to parse LLM analysis: {e}")
            return {
                'fixable': False,
                'error_type': 'unknown',
                'reason': 'Failed to analyze error'
            }
    
    def _apply_fix(self, code: str, analysis: Dict[str, Any]) -> str:
        """Apply fix to code based on analysis"""
        
        fix_strategy = analysis.get('fix_strategy', '')
        
        if fix_strategy == 'increase_timeout':
            return self._fix_timeout(code)
        elif fix_strategy == 'fix_locator':
            return self._fix_locator(code, analysis)
        elif fix_strategy == 'wait_for_visible':
            return self._add_wait_for_visible(code)
        elif fix_strategy == 'strict_mode_fix':
            return self._fix_strict_mode(code)
        else:
            # Use LLM to generate the fix
            return self._apply_fix_with_llm(code, analysis)
    
    def _fix_timeout(self, code: str) -> str:
        """Increase timeout values in code"""
        # Increase page.set_default_timeout
        code = re.sub(
            r'page\.set_default_timeout\((\d+)\)',
            lambda m: f'page.set_default_timeout({int(m.group(1)) * 2})',
            code
        )
        
        # Increase specific timeout parameters
        code = re.sub(
            r'timeout=(\d+)',
            lambda m: f'timeout={int(m.group(1)) * 2}',
            code
        )
        
        return code
    
    def _fix_strict_mode(self, code: str) -> str:
        """Add .first() to locators that might match multiple elements"""
        # Find locator calls without .first() or .nth()
        pattern = r'(page\.(get_by_\w+|locator)\([^)]+\))(?!\.(?:first|nth|count|all)\(\))'
        
        def add_first(match):
            locator = match.group(1)
            # Don't add .first() to simple getters like get_by_test_id
            if 'get_by_test_id' in locator or 'get_by_label' in locator:
                return locator
            return f"{locator}.first()"
        
        return re.sub(pattern, add_first, code)
    
    def _add_wait_for_visible(self, code: str) -> str:
        """Add wait_for visibility checks before interactions"""
        # This is complex - for now, just add a delay
        # In real implementation, would parse AST and add waits
        return code
    
    def _fix_locator(self, code: str, analysis: Dict[str, Any]) -> str:
        """Fix broken locators"""
        # This would require more sophisticated analysis
        # For now, return unchanged
        return code
    
    def _apply_fix_with_llm(self, code: str, analysis: Dict[str, Any]) -> str:
        """Use LLM to apply complex fixes"""
        
        prompt = f"""Fix this script based on the analysis:

Code:
```python
{code}
```

Analysis:
```json
{json.dumps(analysis)}
```

Return the fixed Python code only."""
        
        response = self.llm_client.chat.completions.create(
            model="gpt-4o",
            max_tokens=8192,
            temperature=0.1,
            messages=[{"role": "user", "content": prompt}]
        )
        
        # Extract code from OpenAI response
        text = response.choices[0].message.content if response.choices[0].message.content else ""
        
        # Extract Python code block
        python_pattern = r'```python\s*\n(.*?)\n```'
        matches = re.findall(python_pattern, text, re.DOTALL)
        
        if matches:
            return matches[0].strip()
        
        return code  # Return unchanged if fix failed
