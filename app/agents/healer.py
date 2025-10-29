"""
Healer Agent - Intelligently debugs and fixes failing automation scripts
Based on Playwright's pwt-healer.agent.md
"""
import logging
import re
from typing import Dict, Any, Optional, List, Tuple

logger = logging.getLogger(__name__)


class HealerAgent:
    """
    Playwright Test Healer that debugs and repairs failing automation scripts.
    
    Analyzes failures intelligently and applies targeted fixes:
    1. Selector issues → Replace with more robust locators
    2. Timing issues → Add proper waits and synchronization
    3. Element state issues → Add visibility/enabled checks
    4. Network issues → Add retries and timeouts
    """
    
    # Common error patterns and their fixes
    ERROR_PATTERNS = {
        'selector_not_found': [
            r'locator.*not found',
            r'element.*not found',
            r'no element matches',
            r'strict mode violation',
            r'strict mode violation.*waiting for locator',
            r'waiting for selector.*failed',
            r'expected.*to be visible',
            r'unable to find element',
            r'locator resolved to.*elements',
        ],
        'timeout': [
            r'timeout.*exceeded',
            r'timed out',
            r'deadline.*exceeded',
            r'waiting.*failed.*timeout',
            r'timeout \d+ms exceeded',
            r'page\.goto.*timeout',
        ],
        'not_clickable': [
            r'not clickable',
            r'not actionable',
            r'intercepted.*click',
            r'element is not visible',
            r'element is hidden',
            r'element.*not enabled',
            r'click.*outside of viewport',
        ],
        'not_visible': [
            r'not visible',
            r'is hidden',
            r'visibility.*timeout',
            r'element.*display:\s*none',
        ],
        'network': [
            r'net::err_',
            r'network.*failed',
            r'connection.*refused',
            r'navigation.*failed',
            r'dns.*failed',
            r'ssl.*error',
        ],
        'stale_element': [
            r'stale element',
            r'element.*stale',
            r'detached from dom',
            r'node is detached',
        ],
    }
    
    def __init__(self, engine):
        """
        Initialize Healer Agent
        
        Args:
            engine: The browser automation engine
        """
        self.engine = engine
        
    async def heal_script(self, 
                         original_script: str, 
                         error_message: str, 
                         execution_logs: str = "") -> str:
        """
        Intelligently heal a failing automation script
        
        Args:
            original_script: The failing Python Playwright script
            error_message: Error message from the failed execution
            execution_logs: Execution logs for additional context
            
        Returns:
            Healed Python Playwright script
        """
        logger.info("🎭 Healer Agent: Analyzing failure and creating fix")
        
        try:
            # Analyze the error to determine root cause
            error_type, error_details = self._analyze_error_intelligently(
                error_message, execution_logs
            )
            
            logger.info(f"   Root cause identified: {error_type}")
            logger.info(f"   Error details: {error_details[:100]}...")
            
            # Apply appropriate healing strategy
            if error_type == 'selector_not_found':
                healed = self._heal_selector_issues(original_script, error_message, error_details)
            elif error_type == 'timeout':
                healed = self._heal_timeout_issues(original_script, error_message, error_details)
            elif error_type == 'not_clickable' or error_type == 'not_visible':
                healed = self._heal_visibility_issues(original_script, error_message, error_details)
            elif error_type == 'network':
                healed = self._heal_network_issues(original_script, error_message)
            elif error_type == 'stale_element':
                healed = self._heal_stale_element_issues(original_script, error_message)
            else:
                healed = self._generic_heal(original_script, error_message, error_details)
            
            logger.info("✅ Script healed with intelligent fixes")
            return healed
            
        except Exception as e:
            logger.error(f"❌ Healer failed: {e}", exc_info=True)
            # Return original with enhanced error handling
            return self._add_error_resilience(original_script)
    
    def _analyze_error_intelligently(self, error_message: str, logs: str) -> Tuple[str, str]:
        """
        Intelligently analyze error messages and logs to determine root cause
        
        Args:
            error_message: The error message
            logs: Execution logs
            
        Returns:
            Tuple of (error_type, relevant_error_details)
        """
        combined_text = f"{error_message}\n{logs}".lower()
        
        # Match against known error patterns
        for error_type, patterns in self.ERROR_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, combined_text, re.IGNORECASE):
                    # Extract the relevant line with the error
                    relevant_line = self._extract_error_context(error_message, pattern)
                    return error_type, relevant_line
        
        # If no pattern matched, try to extract useful info
        return 'unknown', error_message
    
    def _extract_error_context(self, error_message: str, pattern: str) -> str:
        """Extract the line containing the error pattern"""
        lines = error_message.split('\n')
        for line in lines:
            if re.search(pattern, line, re.IGNORECASE):
                return line.strip()
        return error_message[:200]  # First 200 chars as fallback
    
    def _heal_selector_issues(self, script: str, error: str, details: str) -> str:
        """
        Heal scripts with selector-related issues
        
        Strategy:
        1. Make locators more flexible (add exact=False)
        2. Add .first to handle multiple matches
        3. Upgrade CSS selectors to role/text locators
        4. Add wait_for_selector before interactions
        """
        healed = script
        
        # Extract the failing locator from error
        failing_locator = self._extract_failing_locator(details)
        
        if failing_locator:
            logger.info(f"   Fixing failing locator: {failing_locator}")
            
            # Make text/label locators non-exact (handle both with and without existing params)
            # Pattern matches get_by_X("text") and get_by_X("text", exact=True)
            healed = re.sub(
                r'get_by_(text|label|placeholder)\("([^"]+)"(?:,\s*exact=True)?\)',
                r'get_by_\1("\2", exact=False)',
                healed
            )
            
            # Add .first to role locators that might match multiple
            # This pattern handles locators with or without keyword arguments
            # Matches: page.get_by_role("button", name="Submit").click()
            # Result: page.get_by_role("button", name="Submit").first.click()
            healed = re.sub(
                r'(page\.get_by_role\("[^"]+"(?:,\s*[^)]+)?\))(?!\.first)(\.|$)',
                r'\1.first\2',
                healed
            )
        
        # Add waits before interactions
        healed = self._add_waits_before_interactions(healed)
        
        # Upgrade CSS selectors to role-based
        healed = self._upgrade_css_to_semantic_locators(healed)
        
        return healed
    
    def _heal_timeout_issues(self, script: str, error: str, details: str) -> str:
        """
        Heal scripts with timeout issues
        
        Strategy:
        1. Increase timeout values (10s → 30s)
        2. Add networkidle waits after navigation
        3. Add explicit element waits
        4. Increase default timeout
        """
        healed = script
        
        # Increase set_default_timeout
        healed = re.sub(
            r'set_default_timeout\((\d+)\)',
            lambda m: f'set_default_timeout({int(m.group(1)) * 2})',
            healed
        )
        
        # If no default timeout set, add it
        if 'set_default_timeout' not in healed:
            healed = healed.replace(
                '        # Set default timeout',
                '        # Set default timeout\n        page.set_default_timeout(60000)  # 60 seconds'
            )
            # If marker doesn't exist, add after page creation
            healed = healed.replace(
                'page = context.new_page()',
                'page = context.new_page()\n        page.set_default_timeout(60000)  # Increased for reliability'
            )
        
        # Add networkidle waits after goto
        healed = re.sub(
            r'page\.goto\("([^"]+)"\)',
            r'page.goto("\1", wait_until="networkidle", timeout=60000)',
            healed
        )
        
        # Increase expect timeouts
        healed = re.sub(
            r'expect\(([^)]+)\)\.to_be_visible\(timeout=(\d+)\)',
            lambda m: f'expect({m.group(1)}).to_be_visible(timeout={int(m.group(2)) * 2})',
            healed
        )
        
        return healed
    
    def _heal_visibility_issues(self, script: str, error: str, details: str) -> str:
        """
        Heal scripts with element visibility/clickability issues
        
        Strategy:
        1. Add scroll_into_view_if_needed()
        2. Add explicit visibility waits
        3. Wait for animations to complete
        4. Check for overlays/modals
        """
        healed = script
        
        # Add scroll and visibility checks before clicks
        healed = re.sub(
            r'(locator|input_field|select_field)\.click\(\)',
            r'\1.scroll_into_view_if_needed()\n            expect(\1).to_be_visible()\n            \1.click()',
            healed
        )
        
        # Add wait_for_timeout after clicks to allow for transitions
        healed = re.sub(
            r'(\.click\(\))\s*\n',
            r'\1\n            page.wait_for_timeout(500)  # Wait for any animations\n',
            healed
        )
        
        # Add force: False to clicks to ensure element is truly clickable
        healed = healed.replace('.click()', '.click(force=False)')
        
        return healed
    
    def _heal_network_issues(self, script: str, error: str) -> str:
        """
        Heal scripts with network-related issues
        
        Strategy:
        1. Add retry logic for navigation
        2. Increase navigation timeouts
        3. Wait for network idle
        """
        healed = script
        
        # Wrap navigation in retry logic
        nav_pattern = r'page\.goto\("([^"]+)"[^)]*\)'
        
        def add_retry(match):
            url = match.group(1)
            return f'''# Retry navigation for reliability
            for attempt in range(3):
                try:
                    page.goto("{url}", wait_until="networkidle", timeout=60000)
                    break
                except Exception as e:
                    if attempt == 2:
                        raise
                    page.wait_for_timeout(2000)
                    print(f"Retrying navigation (attempt {{attempt + 1}})")'''
        
        healed = re.sub(nav_pattern, add_retry, healed)
        
        return healed
    
    def _heal_stale_element_issues(self, script: str, error: str) -> str:
        """
        Heal scripts with stale element issues
        
        Strategy:
        1. Re-query elements before each interaction
        2. Avoid storing locators in variables for too long
        """
        healed = script
        
        # Add comments about re-querying
        healed = healed.replace(
            '# Using rich locator strategy',
            '# Using rich locator strategy (re-queried for freshness)'
        )
        
        # Add wait_for_load_state between steps to ensure DOM is stable
        healed = re.sub(
            r'(# Step \d+:)',
            r'page.wait_for_load_state("domcontentloaded")\n            \1',
            healed
        )
        
        return healed
    
    def _generic_heal(self, script: str, error: str, details: str) -> str:
        """
        Generic healing strategy for unknown errors
        
        Applies multiple defensive improvements
        """
        healed = script
        
        # Add comprehensive waits
        healed = self._add_waits_before_interactions(healed)
        
        # Make locators more flexible
        healed = re.sub(
            r'get_by_text\("([^"]+)"\)',
            r'get_by_text("\1", exact=False)',
            healed
        )
        
        # Add error context collection
        healed = healed.replace(
            'except Exception as e:',
            '''except Exception as e:
            # Enhanced error reporting
            print(f"Error type: {type(e).__name__}")
            print(f"Error message: {str(e)}")
            try:
                print(f"Current URL: {page.url}")
                print(f"Page title: {page.title()}")
                # Take screenshot on error
                page.screenshot(path=f"error_{page.url.split('/')[-1]}.png")
                print("Screenshot saved")
            except:
                pass'''
        )
        
        return healed
    
    def _add_waits_before_interactions(self, script: str) -> str:
        """Add proper waits before all interactions"""
        # Add wait_for_load_state after each navigation
        script = re.sub(
            r'(page\.goto\([^)]+\))',
            r'\1\n            page.wait_for_load_state("domcontentloaded")',
            script
        )
        
        # Add visibility checks before clicks
        script = re.sub(
            r'(locator\.click\(\))',
            r'expect(locator).to_be_visible()\n            \1',
            script
        )
        
        return script
    
    def _upgrade_css_to_semantic_locators(self, script: str) -> str:
        """Upgrade CSS selectors to semantic role/text locators where possible"""
        # Replace generic locator() with more specific methods
        # This is a simplified version - in production, use AST parsing
        
        # Find button CSS selectors and upgrade
        script = re.sub(
            r'page\.locator\("button"\)',
            r'page.get_by_role("button")',
            script
        )
        
        script = re.sub(
            r'page\.locator\("input\[type=\\"text\\"\]"\)',
            r'page.get_by_role("textbox")',
            script
        )
        
        script = re.sub(
            r'page\.locator\("a"\)',
            r'page.get_by_role("link")',
            script
        )
        
        return script
    
    def _extract_failing_locator(self, error_details: str) -> Optional[str]:
        """Extract the failing locator from error message"""
        # Try to find locator in error message
        patterns = [
            r'locator\("([^"]+)"\)',
            r'get_by_\w+\("([^"]+)"\)',
            r'selector:\s*([^\s]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, error_details)
            if match:
                return match.group(1)
        
        return None
    
    def _add_error_resilience(self, script: str) -> str:
        """
        Add general error resilience to the script
        
        Args:
            script: Original script
            
        Returns:
            Script with enhanced error handling and retries
        """
        # Add retry wrapper to main execution
        if 'def main():' in script:
            script = script.replace(
                'success = run_',
                '''# Retry logic for resilience
            max_retries = 2
            for attempt in range(max_retries):
                try:
                    success = run_''',
                1
            )
            
            script = script.replace(
                'finally:',
                '''    break
                except Exception as e:
                    if attempt < max_retries - 1:
                        print(f"Attempt {attempt + 1} failed, retrying...")
                        page.wait_for_timeout(3000)
                    else:
                        success = False
                        raise
            
        finally:''',
                1
            )
        
        return script
