"""
Optimized Browser-Use Engine
AI-powered browser automation with advanced features and optimizations

New Features:
- Advanced browser capabilities (screenshots, PDFs, cookies, sessions)
- Enhanced popup handling with configurable timeouts
- Smart retry mechanism with exponential backoff
- State management for complex workflows
- Data extraction capabilities
- Performance monitoring and metrics
"""
import os
import asyncio
import configparser
import logging
import time
from pathlib import Path
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

# PRIVACY: Disable all external data transmission BEFORE importing browser-use
# This prevents telemetry and cloud sync from being initialized
os.environ.setdefault('ANONYMIZED_TELEMETRY', 'false')
os.environ.setdefault('BROWSER_USE_CLOUD_SYNC', 'false')
from browser_use import Agent, Browser
from browser_use.llm import ChatOpenAI
from auth.oauth_handler import get_oauth_token_with_retry
from app.utils.logging_config import (
    should_log_llm_requests, 
    should_log_llm_responses,
    should_log_browser_actions,
    should_log_page_state,
    should_log_performance
)

# Import ChatBrowserUse for optimized browser automation (3-5x faster)
try:
    from browser_use.llm import ChatBrowserUse
    CHAT_BROWSER_USE_AVAILABLE = True
except ImportError:
    CHAT_BROWSER_USE_AVAILABLE = False

from app.engines.browser_use.advanced_features import AdvancedBrowserFeatures
from app.engines.browser_use.retry_mechanism import RetryConfig, RetryMechanism
from app.engines.browser_use.state_manager import WorkflowState
from app.engines.browser_use.data_extractor import DataExtractor
from app.engines.browser_use.performance_monitor import PerformanceMonitor

project_root = Path(__file__).parent.parent
env_path = project_root / '.env'
load_dotenv(dotenv_path=env_path, override=True)

logger = logging.getLogger(__name__)


class OptimizedBrowserUseEngine:
    """
    Optimized browser automation engine with advanced capabilities
    
    Features:
    - Screenshot capture and PDF generation
    - Cookie and session management
    - Smart retry with exponential backoff
    - Workflow state persistence
    - Data extraction (tables, lists, metadata)
    - Performance monitoring
    - Enhanced popup handling
    """
    
    def __init__(self, headless: bool = False, enable_advanced_features: bool = True):
        """
        Initialize Optimized Browser-Use Engine
        
        Args:
            headless: Run browser in headless mode
            enable_advanced_features: Enable advanced capabilities
        """
        self.headless = headless
        self.enable_advanced_features = enable_advanced_features
        
        config = configparser.ConfigParser()
        config.read('config/config.ini')
        
        gateway_base_url = os.environ.get('GW_BASE_URL')
        if not gateway_base_url:
            raise ValueError("GW_BASE_URL must be set as environment variable to connect to the gateway endpoint.")
        
        try:
            oauth_token = get_oauth_token_with_retry(max_retries=3)
        except Exception as e:
            raise ValueError(f"Failed to obtain OAuth token: {str(e)}. Please check your OAuth configuration.")
        
        model = config.get('openai', 'model', fallback='gpt-4.1-2025-04-14-eastus-dz')
        timeout = int(config.get('openai', 'timeout', fallback='180'))
        self.max_steps = int(config.get('agent', 'max_steps', fallback='25'))
        
        # Logging flags
        self.log_llm_requests = should_log_llm_requests()
        self.log_llm_responses = should_log_llm_responses()
        self.log_browser_actions = should_log_browser_actions()
        self.log_page_state = should_log_page_state()
        self.log_performance = should_log_performance()
        
        # Verification keywords to detect validation requirements
        self.verification_keywords = [
            'verify', 'check', 'ensure', 'validate', 'assert', 
            'confirm', 'test', 'must', 'should contain', 'should have',
            'expect', 'required', 'make sure', 'assert that'
        ]
        
        # Browser performance settings - using reliable defaults
        self.minimum_wait_page_load_time = float(config.get('browser_performance', 'minimum_wait_page_load_time', fallback='1.0'))
        self.wait_for_network_idle_page_load_time = float(config.get('browser_performance', 'wait_for_network_idle_page_load_time', fallback='1.5'))
        self.wait_between_actions = float(config.get('browser_performance', 'wait_between_actions', fallback='1.0'))
        
        # Use ChatBrowserUse model if enabled (3-5x faster for browser automation)
        use_chat_browser_use = config.getboolean('openai', 'use_chat_browser_use', fallback=False)
        
        if use_chat_browser_use and CHAT_BROWSER_USE_AVAILABLE:
            logger.info("🚀 Using ChatBrowserUse optimized model (3-5x faster)")
            self.llm = ChatBrowserUse()
        else:
            if use_chat_browser_use and not CHAT_BROWSER_USE_AVAILABLE:
                logger.warning("⚠️  ChatBrowserUse not available, falling back to standard OpenAI model")
            logger.info(f"Using gateway model: {model} via {gateway_base_url}")
            self.llm = ChatOpenAI(
                model=model,
                base_url=gateway_base_url,
                api_key=oauth_token,
                default_headers={
                    "Authorization": f"Bearer {oauth_token}"
                },
                timeout=timeout
            )
        
        if enable_advanced_features:
            output_dir = config.get('advanced_features', 'output_directory', fallback='automation_outputs')
            self.enable_screenshots = config.getboolean('advanced_features', 'enable_screenshots', fallback=True)
            self.per_step_screenshots = config.getboolean('advanced_features', 'per_step_screenshots', fallback=False)
            self.enable_pdf_generation = config.getboolean('advanced_features', 'enable_pdf_generation', fallback=True)
            self.enable_cookie_management = config.getboolean('advanced_features', 'enable_cookie_management', fallback=True)
            self.enable_state_persistence = config.getboolean('advanced_features', 'enable_state_persistence', fallback=True)
            
            self.advanced_features = AdvancedBrowserFeatures(output_dir=output_dir)
            
            max_retries = int(config.get('retry', 'max_retries', fallback='3'))
            initial_delay = float(config.get('retry', 'initial_delay', fallback='1.0'))
            max_delay = float(config.get('retry', 'max_delay', fallback='30.0'))
            backoff_factor = float(config.get('retry', 'backoff_factor', fallback='2.0'))
            
            retry_config = RetryConfig(
                max_retries=max_retries,
                initial_delay=initial_delay,
                max_delay=max_delay,
                backoff_factor=backoff_factor
            )
            self.retry_mechanism = RetryMechanism(retry_config)
            
            track_metrics = config.getboolean('performance', 'track_detailed_metrics', fallback=True)
            self.performance_monitor = PerformanceMonitor(track_detailed_metrics=track_metrics)
            
            self.data_extractor = DataExtractor()
            self.workflow_state = None
            
            logger.info("🚀 Advanced features enabled: Screenshots, PDFs, Cookies, Retry, Performance Tracking")
        else:
            logger.info("ℹ️  Running in basic mode (advanced features disabled)")
    
    def _convert_to_web_path(self, filesystem_path: str) -> str:
        """
        Convert a filesystem path to a web-accessible URL path
        
        Args:
            filesystem_path: Local filesystem path (e.g., './screenshots/step_1.png')
            
        Returns:
            Web-accessible path (e.g., 'screenshots/step_1.png')
        """
        import os
        
        # Normalize path separators to forward slashes
        web_path = filesystem_path.replace('\\', '/')
        
        # Remove leading './' if present
        if web_path.startswith('./'):
            web_path = web_path[2:]
        
        # Extract just the filename from the full path if it contains directories
        # e.g., 'automation_outputs/screenshots/step_1.png' or 'screenshots/step_1.png'
        if 'screenshots/' in web_path:
            # Find 'screenshots/' and take everything from there
            idx = web_path.find('screenshots/')
            web_path = web_path[idx:]
        elif 'automation_outputs/' in web_path:
            # Keep the full path for automation_outputs
            idx = web_path.find('automation_outputs/')
            web_path = web_path[idx:]
        
        return web_path
    
    def _has_verification_requirements(self, instruction: str) -> bool:
        """
        Check if the instruction contains verification/validation requirements
        
        Args:
            instruction: User's instruction
            
        Returns:
            True if instruction contains verification keywords
        """
        instruction_lower = instruction.lower()
        return any(keyword in instruction_lower for keyword in self.verification_keywords)
    
    def _check_verification_failure(self, final_result: Any, steps: List[Dict], instruction: str) -> Optional[Dict[str, Any]]:
        """
        Check if verification failed based on final result and steps
        
        Args:
            final_result: Final result from agent execution
            steps: List of executed steps
            instruction: Original instruction
            
        Returns:
            Dict with verification failure info if detected, None otherwise
        """
        if not final_result:
            return None
        
        result_str = str(final_result).lower()
        
        # First check for explicit success indicators - if found, verification passed
        success_indicators = [
            'verification passed', 'check passed', 'verified successfully',
            'validation passed', 'assertion passed', 'confirmed successfully'
        ]
        if any(indicator in result_str for indicator in success_indicators):
            return None  # Verification explicitly passed
        
        # More specific failure indicators to avoid false positives
        failure_indicators = [
            'verification failed', 'check failed', 'assertion failed',
            'validation failed', 'not found', 'does not exist',
            'could not find', 'unable to find', 'did not find',
            'missing element', 'element missing', 'cannot locate',
            'no such element', 'not present on', 'not visible',
            'failed to verify', 'failed to validate', 'failed to confirm'
        ]
        
        has_verification = self._has_verification_requirements(instruction)
        has_failure = any(indicator in result_str for indicator in failure_indicators)
        
        if has_verification and has_failure:
            return {
                'verification_failed': True,
                'reason': str(final_result)[:300],  # Limit length
                'instruction': instruction,
                'completed_steps': len(steps)
            }
        
        return None
    
    async def execute_instruction(self, instruction: str, 
                                  workflow_id: Optional[str] = None,
                                  save_screenshot: bool = False,
                                  save_pdf: bool = False,
                                  progress_callback=None) -> Dict[str, Any]:
        """
        Execute a natural language instruction with advanced features
        
        Args:
            instruction: User's natural language instruction
            workflow_id: Optional workflow ID for state management
            save_screenshot: Capture screenshot after completion
            save_pdf: Generate PDF after completion
            progress_callback: Optional callback for progress updates
            
        Returns:
            Dictionary with execution results and advanced metrics
        """
        # Input validation
        if not instruction or not instruction.strip():
            logger.error("❌ Empty instruction provided")
            return {
                "success": False,
                "error": "Instruction cannot be empty",
                "error_type": "ValidationError",
                "steps": [],
                "iterations": 0
            }
        
        instruction = instruction.strip()
        op_id = None
        browser = None
        if self.enable_advanced_features:
            op_id = self.performance_monitor.start_operation("execute_instruction")
            
            if workflow_id:
                self.workflow_state = WorkflowState(workflow_id=workflow_id, persist_to_disk=True)
        
        try:
            logger.info("🤖 Initializing Browser-Use Agent")
            logger.info(f"📋 Task: {instruction}")
            logger.info(f"🔢 Max steps: {self.max_steps}")
            
            # Send initialization progress
            if progress_callback:
                progress_callback('init', {'message': 'Initializing browser automation agent...', 'instruction': instruction})
            
            # System instructions optimized for efficiency while maintaining safety
            # Fix from https://github.com/browser-use/browser-use/pull/235 to prevent going beyond task
            system_instructions = f"""
YOUR ULTIMATE TASK: "{instruction}"

⚠️ CRITICAL - GOAL-BASED EXECUTION ⚠️
Identify the GOAL of the task, then stop immediately once that goal is achieved.
You MAY make auxiliary decisions to achieve the goal (wait for pages, handle popups, retry actions).
You MUST NOT perform actions beyond achieving the stated goal.

EXECUTION APPROACH:
1. Parse the task to identify the GOAL (the end state to achieve)
2. Make necessary auxiliary decisions to reach that goal:
   ✅ Wait for pages to load
   ✅ Handle popups or dialog boxes that block progress
   ✅ Retry failed actions (element not found, slow page load)
   ✅ Navigate through necessary intermediate steps
3. Once the GOAL is achieved → IMMEDIATELY use done()
4. Do NOT perform additional "helpful" actions beyond the goal

EXAMPLES OF GOAL-BASED EXECUTION:

Task: "open linkedin.com click join now"
→ GOAL: Click the "join now" button on LinkedIn
→ ✅ Correct: Navigate to linkedin.com → Wait for page → Click "join now" → Verify click succeeded → done()
→ ❌ Wrong: Navigate → Click "join now" → Fill email → Fill password (GOAL was already achieved after clicking!)

Task: "go to amazon.com and search for laptop"
→ GOAL: Execute a search for "laptop" on Amazon
→ ✅ Correct: Navigate → Wait for page → Type "laptop" in search → Click search button → done()
→ ❌ Wrong: Navigate → Search → Click first result → View product details (GOAL was achieved after search!)

Task: "fill in the email field with test@example.com and submit the form"
→ GOAL: Submit form with email filled
→ ✅ Correct: Fill email → Click submit → Wait for submission → done()
→ ❌ Wrong: Stop after filling email (GOAL requires submitting!)

CRITICAL: STOP IMMEDIATELY AFTER GOAL IS ACHIEVED
→ Do NOT fill forms unless required to achieve the goal
→ Do NOT click buttons unless required to achieve the goal
→ Do NOT navigate to pages unless required to achieve the goal
→ Ask yourself: "Have I achieved the stated goal?" If yes → done()

AUXILIARY DECISIONS (ALLOWED):
- Waiting for pages/elements to load
- Handling popups that block the goal
- Retrying actions that fail due to timing
- Navigating to intermediate pages to reach the goal
- Verifying that actions succeeded

PAGE LOADING & ERRORS:
- If element not found → page still loading → wait 2s → retry with fresh page state
- Verify critical actions succeeded before done()
- If action fails after retries → report failure and use done()

⚠️ INTELLIGENT DROPDOWN HANDLING ⚠️
When interacting with dropdown lists or select elements, use these strategies:

1. NATIVE HTML SELECT ELEMENTS:
   - Use select_option() or click() to interact with <select> elements
   - You can select by visible text, value attribute, or index
   - Example: Select "United States" from country dropdown
   
2. CUSTOM JAVASCRIPT DROPDOWNS (Material-UI, Ant Design, etc.):
   - First click to open the dropdown
   - Wait for dropdown options to appear (wait 0.5-1s)
   - Then click on the desired option
   - For long dropdowns, scroll into view before clicking
   
3. DROPDOWN WITH SEARCH/FILTER:
   - Click to open dropdown
   - Type search text to filter options
   - Wait for filtered results to appear
   - Click the desired option
   
4. HANDLING LONG DROPDOWN LISTS:
   - If option not visible, scroll within dropdown container
   - Use hover() on options to scroll them into view
   - For very long lists, use search/filter if available
   
5. MULTI-SELECT DROPDOWNS:
   - Click each option to add to selection
   - Don't close dropdown until all selections are made
   - Look for "Select All" or "Clear All" buttons if available

DROPDOWN TROUBLESHOOTING:
- If click doesn't open dropdown → try hovering first, then click
- If option not found → check if it's dynamically loaded, wait longer
- If dropdown closes unexpectedly → use longer waits between actions
- For custom dropdowns, look for aria-expanded, role="listbox", or similar attributes

⚠️ VERIFICATION & VALIDATION REQUIREMENTS ⚠️
If the task contains verification keywords (verify, check, ensure, validate, assert, confirm, must, should):
- You MUST explicitly check the verification condition
- If verification FAILS → Report failure clearly with: "Verification failed: [specific reason]"
- If verification SUCCEEDS → Report success clearly with: "Verification passed: [what was verified]"
- NEVER ignore verification requirements - they are critical to task success
- Examples:
  * "verify the search button exists" → If button not found, report: "Verification failed: search button not found"
  * "ensure page contains 'Welcome'" → If text not found, report: "Verification failed: 'Welcome' text not present on page"

SECURITY:
- Never navigate to unintended domains
- Confirm sensitive actions before executing
            """
            
            logger.info("⚙️  Configuring agent with optimizations")
            
            # Send browser initialization progress
            if progress_callback:
                progress_callback('browser_init', {'message': f'Starting browser (headless={self.headless})...'})
            
            # Create browser instance with optimized performance settings
            # Browser accepts **data kwargs, type stubs might not reflect all parameters
            browser = Browser(  # type: ignore
                headless=self.headless,
                disable_security=False,  # Keep security enabled for production
                minimum_wait_page_load_time=self.minimum_wait_page_load_time,
                wait_for_network_idle_page_load_time=self.wait_for_network_idle_page_load_time,
                wait_between_actions=self.wait_between_actions
            )
            logger.info(f"🌐 Browser initialized (headless={self.headless})")
            
            # Send agent creation progress
            if progress_callback:
                progress_callback('agent_create', {'message': 'Creating AI agent...'})
            
            agent = Agent(
                task=instruction,
                llm=self.llm,
                browser=browser,  # Pass browser for proper popup/multi-window handling
                extend_system_message=system_instructions.strip(),
            )
            
            logger.info("▶️  Starting agent execution...")
            
            # Send execution start progress
            if progress_callback:
                progress_callback('execution_start', {'message': 'Agent is now executing automation steps...'})
            
            # Add detailed logging wrapper for agent.run()
            if self.log_performance:
                start_time = time.time()
            
            logger.debug("=" * 80)
            logger.debug("🔄 CALLING agent.run() - LLM will be invoked repeatedly")
            logger.debug(f"Max steps: {self.max_steps}")
            logger.debug(f"Task: {instruction}")
            logger.debug("=" * 80)
            
            try:
                if self.enable_advanced_features:
                    @self.retry_mechanism.async_retry
                    async def run_with_retry():
                        return await agent.run(max_steps=self.max_steps)
                    
                    history = await run_with_retry()
                else:
                    history = await agent.run(max_steps=self.max_steps)
            except Exception as e:
                logger.error("=" * 80)
                logger.error("❌ AGENT.RUN() FAILED")
                logger.error(f"Error Type: {type(e).__name__}")
                logger.error(f"Error Message: {str(e)}")
                logger.error("=" * 80)
                import traceback
                logger.error(traceback.format_exc())
                raise
            
            if self.log_performance:
                elapsed = time.time() - start_time
                logger.debug(f"⏱️  agent.run() completed in {elapsed:.2f}s")
            
            logger.info(f"⏹️  Agent execution completed")
            
            logger.info("=" * 80)
            logger.info("📋 EXECUTION STEPS")
            logger.info("=" * 80)
            steps = []
            screenshot_paths = []
            
            for i, item in enumerate(history.history):
                step_num = i + 1
                action = str(getattr(item, 'model_output', ''))
                state = str(getattr(item, 'state', ''))
                
                # Concise step-based logging
                logger.info(f"Step {step_num}: {action[:120]}")
                
                step = {
                    "tool": "browser_use_action",
                    "arguments": {"action": action},
                    "success": True,
                    "result": {
                        "state": state,
                        "step_number": step_num
                    }
                }
                steps.append(step)
                
                # Send step progress update
                if progress_callback:
                    progress_callback('step', {
                        'step_number': step_num,
                        'action': action[:150],
                        'total_steps': len(history.history)
                    })
                
                # Capture screenshot after each step (only if per_step_screenshots is enabled)
                if self.enable_advanced_features and browser and self.per_step_screenshots:
                    try:
                        page = await browser.get_current_page()
                        if page:
                            screenshot_name = f"step_{step_num}"
                            screenshot_result = await self.advanced_features.capture_screenshot(page, name=screenshot_name)
                            if screenshot_result.get('success'):
                                screenshot_path = screenshot_result.get('path')
                                screenshot_paths.append(screenshot_path)
                                logger.info(f"📸 Step {step_num} screenshot captured: {screenshot_path}")
                                
                                # Convert filesystem path to web URL
                                web_path = self._convert_to_web_path(screenshot_path)
                                
                                # Send screenshot event via progress callback
                                if progress_callback:
                                    progress_callback('screenshot', {
                                        'path': web_path,
                                        'url': screenshot_result.get('url', ''),
                                        'step_number': step_num
                                    })
                    except Exception as screenshot_error:
                        logger.warning(f"⚠️  Step {step_num} screenshot capture failed: {screenshot_error}")
                
                if self.enable_advanced_features and self.workflow_state:
                    self.workflow_state.add_step(
                        step_name=f"browser_action_{step_num}",
                        step_data={"action": action},
                        success=True
                    )
            
            final_result = history.final_result() if hasattr(history, 'final_result') else None
            
            # Capture final screenshot if per_step_screenshots is disabled
            # This ensures we always have at least one screenshot showing the final result
            if self.enable_advanced_features and browser and not self.per_step_screenshots and len(steps) > 0:
                try:
                    page = await browser.get_current_page()
                    if page:
                        screenshot_name = "final_result"
                        screenshot_result = await self.advanced_features.capture_screenshot(page, name=screenshot_name)
                        if screenshot_result.get('success'):
                            screenshot_path = screenshot_result.get('path')
                            screenshot_paths.append(screenshot_path)
                            logger.info(f"📸 Final screenshot captured: {screenshot_path}")
                            
                            # Convert filesystem path to web URL
                            web_path = self._convert_to_web_path(screenshot_path)
                            
                            # Send screenshot event via progress callback
                            if progress_callback:
                                progress_callback('screenshot', {
                                    'path': web_path,
                                    'url': screenshot_result.get('url', ''),
                                    'step_number': len(steps),
                                    'final': True
                                })
                except Exception as screenshot_error:
                    logger.warning(f"⚠️  Final screenshot capture failed: {screenshot_error}")
            
            # Check for verification failures
            verification_failure = self._check_verification_failure(final_result, steps, instruction)
            if verification_failure:
                logger.error("=" * 80)
                logger.error("❌ VERIFICATION FAILED")
                logger.error(f"Instruction: {verification_failure['instruction']}")
                logger.error(f"Reason: {verification_failure['reason']}")
                logger.error(f"Completed Steps: {verification_failure['completed_steps']}")
                logger.error("=" * 80)
                
                # Return verification failure result
                return {
                    "success": False,
                    "error": f"Verification failed: {verification_failure['reason']}",
                    "error_type": "VerificationError",
                    "verification_failed": True,
                    "verification_details": verification_failure,
                    "steps": steps,
                    "iterations": len(steps),
                    "final_result": final_result
                }
            
            # Screenshots are now captured automatically at each step above
            
            logger.info("=" * 80)
            if len(steps) == 0:
                logger.info("❌ Execution Failed — No steps were executed successfully")
                logger.info("=" * 80)
                result = {
                    "success": False,
                    "error": "Browser automation failed to execute any steps",
                    "message": "No steps executed - browser may have failed to start",
                    "steps": [],
                    "iterations": 0,
                    "final_result": None
                }
            else:
                logger.info(f"✅ Execution Completed Successfully")
                logger.info(f"Total Steps: {len(steps)}")
                if final_result:
                    logger.info(f"Result: {str(final_result)[:150]}")
                logger.info("=" * 80)
                
                result = {
                    "success": True,
                    "message": f"Task completed successfully. Executed {len(steps)} steps.",
                    "steps": steps,
                    "iterations": len(steps),
                    "final_result": final_result,
                    "screenshot_paths": screenshot_paths
                }
            
            if self.enable_advanced_features:
                if op_id:
                    self.performance_monitor.end_operation(op_id, success=result["success"])
                
                result["performance_metrics"] = self.performance_monitor.get_summary()
                
                if self.workflow_state:
                    result["workflow_state"] = self.workflow_state.get_summary()
                
                result["retry_stats"] = self.retry_mechanism.get_stats()
            
            return result
            
        except Exception as e:
            error_msg = str(e)
            logger.error("=" * 80)
            logger.error(f"❌ Execution Failed — {type(e).__name__}")
            logger.error(f"Error: {error_msg}")
            logger.error("=" * 80)
            
            if self.enable_advanced_features and op_id:
                self.performance_monitor.end_operation(op_id, success=False)
            
            # Provide helpful error context
            error_context = {
                "success": False,
                "error": error_msg,
                "error_type": type(e).__name__,
                "steps": [],
                "iterations": 0
            }
            
            # Add helpful hints based on error type
            if "timeout" in error_msg.lower():
                error_context["hint"] = "The operation timed out. Consider increasing the timeout or simplifying the task."
            elif "api" in error_msg.lower() or "oauth" in error_msg.lower() or "token" in error_msg.lower():
                error_context["hint"] = "Authentication error. Please check your OAuth configuration (OAUTH_TOKEN_URL, OAUTH_CLIENT_ID, OAUTH_CLIENT_SECRET, etc.)."
            elif "playwright" in error_msg.lower() or "browser" in error_msg.lower():
                error_context["hint"] = "Browser initialization failed. Ensure Playwright is properly installed."
            
            if self.enable_advanced_features:
                error_context["retry_stats"] = self.retry_mechanism.get_stats()
            
            return error_context
        finally:
            # Clean up browser resources
            if browser is not None:
                try:
                    # Browser cleanup is handled automatically by browser-use library
                    # The Browser object manages its own lifecycle
                    logger.debug("🧹 Browser cleanup completed")
                except Exception as cleanup_error:
                    logger.warning(f"⚠️  Error during browser cleanup: {cleanup_error}")
    
    def execute_instruction_sync(self, instruction: str, progress_callback=None, **kwargs) -> Dict[str, Any]:
        """
        Synchronous wrapper for execute_instruction
        
        Args:
            instruction: User's natural language instruction
            progress_callback: Optional callback for progress updates
            **kwargs: Additional arguments for execute_instruction
            
        Returns:
            Dictionary with execution results
        """
        loop = None
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                return loop.run_until_complete(self.execute_instruction(instruction, progress_callback=progress_callback, **kwargs))
            finally:
                # Clean up pending tasks
                pending = asyncio.all_tasks(loop)
                for task in pending:
                    task.cancel()
                # Wait for cancelled tasks to finish
                if pending:
                    loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
                
        except Exception as e:
            logger.error(f"Sync execution error: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": f"Sync execution error: {str(e)}",
                "steps": [],
                "iterations": 0
            }
        finally:
            # Always close the event loop
            if loop is not None:
                try:
                    loop.close()
                    logger.debug("🧹 Event loop closed successfully")
                except Exception as loop_error:
                    logger.warning(f"⚠️  Error closing event loop: {loop_error}")
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance monitoring summary"""
        if self.enable_advanced_features:
            return self.performance_monitor.get_summary()
        return {"error": "Advanced features not enabled"}
    
    def get_retry_stats(self) -> Dict[str, Any]:
        """Get retry mechanism statistics"""
        if self.enable_advanced_features:
            return self.retry_mechanism.get_stats()
        return {"error": "Advanced features not enabled"}
    
    def reset_metrics(self):
        """Reset all performance metrics and statistics"""
        if self.enable_advanced_features:
            self.performance_monitor.reset()
            self.retry_mechanism.reset_stats()
            logger.info("🔄 All metrics reset")
