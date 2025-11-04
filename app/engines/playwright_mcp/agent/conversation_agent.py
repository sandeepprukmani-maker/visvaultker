"""
OpenAI-powered Browser Agent
Interprets natural language instructions and executes browser actions
Uses direct execution mode for browser automation tasks
Includes three-agent workflow for Playwright Python code generation
"""
import json
import os
import logging
import time
import configparser
from pathlib import Path
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from openai import OpenAI
from auth.oauth_handler import get_oauth_token_with_retry
from app.utils.logging_config import (
    should_log_llm_requests, 
    should_log_llm_responses,
    should_log_browser_actions,
    should_log_page_state,
    should_log_performance
)
# Import three-agent system
from app.engines.playwright_mcp.agents import (
    StrictModeLocatorEngine,
    PlannerAgent,
    GeneratorAgent,
    HealerAgent
)
from app.engines.playwright_mcp.code_executor import CodeExecutor
# Load .env file from project root with explicit path
project_root = Path(__file__).parent.parent.parent.parent
env_path = project_root / '.env'
load_dotenv(dotenv_path=env_path, override=True)


class BrowserAgent:
    """
    AI agent that performs browser automation based on natural language instructions
    
    Uses direct execution mode to control browsers via Playwright MCP tools
    """
    
    def __init__(self, mcp_client: Any, workspace_root: str = "."):
        """
        Initialize the Browser Agent
        
        Args:
            mcp_client: MCP client for browser automation
            workspace_root: Root directory for specs/ and tests/ (default: current directory)
        """
        config = configparser.ConfigParser()
        config.read('config/config.ini')
        
        self.mcp_client = mcp_client
        
        gateway_base_url = os.environ.get('GW_BASE_URL')
        if not gateway_base_url:
            raise ValueError("GW_BASE_URL must be set as environment variable to connect to the gateway endpoint.")
        
        try:
            oauth_token = get_oauth_token_with_retry(max_retries=3)
        except Exception as e:
            raise ValueError(f"Failed to obtain OAuth token: {str(e)}. Please check your OAuth configuration.")
        
        self.client = OpenAI(
            base_url=gateway_base_url,
            api_key=oauth_token,
            default_headers={
                "Authorization": f"Bearer {oauth_token}"
            }
        )
        self.model = config.get('openai', 'model', fallback='gpt-4.1-2025-04-14-eastus-dz')
        self.conversation_history = []
        self.max_iterations = config.getint('agent', 'max_steps', fallback=40)
        
        # Expose chat_model for Planner/Generator agents to access
        self.chat_model = self.client
        
        # Logging configuration
        self.logger = logging.getLogger(__name__)
        self.log_llm_requests = should_log_llm_requests()
        self.log_llm_responses = should_log_llm_responses()
        self.log_browser_actions = should_log_browser_actions()
        self.log_page_state = should_log_page_state()
        self.log_performance = should_log_performance()
        
        # Store gateway URL for logging
        self.gateway_base_url = gateway_base_url
        
        # Verification keywords to detect validation requirements
        self.verification_keywords = [
            'verify', 'check', 'ensure', 'validate', 'assert', 
            'confirm', 'test', 'must', 'should contain', 'should have',
            'expect', 'required', 'make sure', 'assert that'
        ]
        
        # Initialize three-agent system for Python code generation
        self.locator_engine = StrictModeLocatorEngine(mcp_client=self.mcp_client)
        self.planner_agent = PlannerAgent(
            mcp_client=self.mcp_client,
            llm_client=self.client,
            locator_engine=self.locator_engine,
            model=self.model
        )
        self.generator_agent = GeneratorAgent(
            llm_client=self.client,
            locator_engine=self.locator_engine,
            model=self.model
        )
        self.healer_agent = HealerAgent(
            llm_client=self.client,
            model=self.model
        )
        self.code_executor = CodeExecutor(timeout=120)
        
        # Enable Python code generation by default for Playwright MCP
        self.generate_python_code = True
        
        # Workflow mode: 'direct' or 'code_first'
        # direct: Execute immediately via MCP, then optionally generate code
        # code_first: Plan → Generate → Execute → Heal (guaranteed working code)
        self.workflow_mode = config.get('playwright_mcp', 'workflow_mode', fallback='direct')
        
        
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
    
    def _check_verification_failure(self, final_message: str, steps: List[Dict], instruction: str) -> Optional[Dict[str, Any]]:
        """
        Check if verification failed based on final message and steps
        
        Args:
            final_message: Final message from LLM
            steps: List of executed steps
            instruction: Original instruction
            
        Returns:
            Dict with verification failure info if detected, None otherwise
        """
        if not final_message:
            return None
        
        message_lower = final_message.lower()
        
        # First check for explicit success indicators - if found, verification passed
        success_indicators = [
            'verification passed', 'check passed', 'verified successfully',
            'validation passed', 'assertion passed', 'confirmed successfully'
        ]
        if any(indicator in message_lower for indicator in success_indicators):
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
        has_failure = any(indicator in message_lower for indicator in failure_indicators)
        
        if has_verification and has_failure:
            return {
                'verification_failed': True,
                'reason': final_message[:300],  # Limit length
                'instruction': instruction,
                'completed_steps': len(steps)
            }
        
        return None
    
    def execute_instruction(self, instruction: str, mode: str = "direct", progress_callback=None) -> Dict[str, Any]:
        """
        Execute a natural language instruction
        
        Args:
            instruction: User's natural language instruction
            mode: Execution mode - "direct" or uses workflow_mode from config
            progress_callback: Optional callback for progress updates
            
        Returns:
            Dictionary with execution results and steps taken
        """
        # Only direct mode is supported now
        if mode != "direct":
            return {
                "success": False,
                "error": f"Invalid mode: {mode}",
                "message": "Only 'direct' mode is supported. Other modes have been removed.",
                "mode": mode
            }
        
        # Check workflow mode configuration
        if self.workflow_mode == 'code_first':
            self.logger.info("🎯 Using Code-First workflow (Plan → Generate → Execute → Heal)")
            # Run async code-first workflow in event loop
            import asyncio
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            return loop.run_until_complete(self._execute_code_first_mode(instruction, progress_callback))
        else:
            self.logger.info("🎯 Using Direct workflow (Execute → Optionally Generate Code)")
            return self._execute_direct_mode(instruction, progress_callback)
    
    
    def _execute_direct_mode(self, instruction: str, progress_callback=None) -> Dict[str, Any]:
        """
        Execute a natural language instruction
        
        Args:
            instruction: User's natural language instruction
            progress_callback: Optional callback for progress updates
            
        Returns:
            Dictionary with execution results and steps taken
        """
        # Send init progress
        if progress_callback:
            progress_callback('init', {'message': 'Initializing Playwright MCP agent...', 'instruction': instruction})
        
        if not self.mcp_client.initialized:
            self.mcp_client.initialize()
        
        # Send browser init progress
        if progress_callback:
            progress_callback('browser_init', {'message': 'Playwright MCP server ready...'})
        
        tools = self.mcp_client.get_tools_schema()
        
        # Send agent create progress
        if progress_callback:
            progress_callback('agent_create', {'message': 'Creating AI conversation agent...'})
        
        self.conversation_history = [
            {
                "role": "system",
                "content": """You are an efficient browser automation assistant. 
Complete the user's task quickly and accurately using the minimum necessary steps.

Instructions:
1. Break down the task into the essential browser automation steps
2. Navigate to websites, interact with elements, and extract data as needed
3. When you see page snapshots in YAML format, use element references like [ref=e1], [ref=e2] for browser_click and browser_fill
4. Complete the task efficiently - avoid unnecessary snapshots or redundant actions
5. Once the task is complete, respond with your completion message (no more tool calls)
6. IMPORTANT: After completing a successful action, move on to the next step - do not repeat successful actions

⚠️ INTELLIGENT DROPDOWN HANDLING ⚠️
When interacting with dropdown lists or select elements, use these strategies:

1. NATIVE HTML SELECT ELEMENTS:
   - Use browser_select with the select element reference
   - Can select by value, label, or index
   - Example: browser_select([ref=e5], value="united-states")
   
2. CUSTOM JAVASCRIPT DROPDOWNS (Material-UI, Ant Design, etc.):
   - First use browser_click to open the dropdown
   - Wait briefly (the browser will handle this)
   - Take a snapshot to see available options
   - Use browser_click on the desired option element
   
3. DROPDOWN WITH SEARCH/FILTER:
   - Click to open dropdown
   - Use browser_fill to type search text in the filter field
   - Take snapshot to see filtered results
   - Click the desired option
   
4. HANDLING LONG DROPDOWN LISTS:
   - If option not visible in snapshot, use browser_scroll to scroll within dropdown
   - Use browser_hover on options to bring them into view
   - For very long lists, prefer search/filter if available
   
5. MULTI-SELECT DROPDOWNS:
   - Click each option to add to selection
   - Don't close dropdown until all selections are made
   - Look for "Select All" or "Clear All" buttons in the snapshot

DROPDOWN TROUBLESHOOTING:
- If click doesn't open dropdown → try browser_hover first, then browser_click
- If option not found → it may be dynamically loaded, take another snapshot after waiting
- If dropdown closes unexpectedly → some dropdowns close on blur, work quickly
- For custom dropdowns, look for elements with aria-expanded, role="listbox", role="option" attributes

⚠️ VERIFICATION & VALIDATION REQUIREMENTS ⚠️
If the task contains verification keywords (verify, check, ensure, validate, assert, confirm, must, should):
- You MUST explicitly check the verification condition using appropriate tools
- If verification FAILS → Report clearly: "Verification failed: [specific reason]"
- If verification SUCCEEDS → Report clearly: "Verification passed: [what was verified]"
- NEVER ignore verification requirements - they are critical to task success
- Examples:
  * "verify the search button exists" → Use browser_snapshot to check, if not found: "Verification failed: search button not found"
  * "ensure page contains 'Welcome'" → Check page content, if missing: "Verification failed: 'Welcome' text not present"

Be precise, fast, and efficient."""
            },
            {
                "role": "user",
                "content": instruction
            }
        ]
        
        steps = []
        iteration = 0
        
        # Send execution start progress
        if progress_callback:
            progress_callback('execution_start', {'message': 'Agent is now executing automation steps...'})
        
        while iteration < self.max_iterations:
            iteration += 1
            
            try:
                # Log LLM request details
                if self.log_llm_requests:
                    self.logger.debug("=" * 80)
                    self.logger.debug(f"📤 LLM REQUEST (Iteration {iteration}/{self.max_iterations})")
                    self.logger.debug(f"Model: {self.model}")
                    self.logger.debug(f"Gateway: {self.gateway_base_url}")
                    self.logger.debug(f"Messages count: {len(self.conversation_history)}")
                    self.logger.debug(f"Tools available: {len(tools)}")
                    self.logger.debug("=" * 80)
                
                if self.log_performance:
                    start_time = time.time()
                
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=self.conversation_history,  # type: ignore
                    tools=tools,
                    tool_choice="auto",
                    max_tokens=4096
                )
                
                if self.log_performance:
                    elapsed = time.time() - start_time
                    self.logger.debug(f"⏱️  LLM response received in {elapsed:.2f}s")
                
                # Log LLM response details
                if self.log_llm_responses:
                    self.logger.debug("=" * 80)
                    self.logger.debug(f"📥 LLM RESPONSE (Iteration {iteration})")
                    self.logger.debug(f"Finish reason: {response.choices[0].finish_reason}")
                    if response.usage:
                        self.logger.debug(f"Tokens - Prompt: {response.usage.prompt_tokens}, Completion: {response.usage.completion_tokens}, Total: {response.usage.total_tokens}")
                    self.logger.debug("=" * 80)
                
                message = response.choices[0].message
                self.conversation_history.append(message.model_dump())
                
                if message.tool_calls:
                    for tool_call in message.tool_calls:
                        tool_name = tool_call.function.name  # type: ignore
                        tool_args = json.loads(tool_call.function.arguments)  # type: ignore
                        
                        # Concise step-based logging for key actions
                        action_desc = self._format_action_description(tool_name, tool_args)
                        self.logger.info(f"Step {len(steps) + 1}: {action_desc}")
                        
                        try:
                            if self.log_performance:
                                action_start = time.time()
                            
                            result = self.mcp_client.call_tool(tool_name, tool_args)
                            
                            if self.log_performance:
                                action_elapsed = time.time() - action_start
                                self.logger.debug(f"⏱️  Action '{tool_name}' completed in {action_elapsed:.2f}s")
                            
                            # Log action result
                            if self.log_browser_actions:
                                self.logger.debug(f"✅ Action '{tool_name}' succeeded")
                                if self.log_page_state and result:
                                    self.logger.debug(f"Result preview: {str(result)[:200]}...")
                            
                            step_info = {
                                "tool": tool_name,
                                "arguments": tool_args,
                                "success": True,
                                "result": result
                            }
                            steps.append(step_info)
                            
                            # Send step progress update
                            if progress_callback:
                                progress_callback('step', {
                                    'step_number': len(steps),
                                    'action': action_desc[:150],
                                    'total_steps': len(steps)
                                })
                            
                            # Capture screenshot after navigation or significant actions
                            if tool_name in ['browser_navigate', 'browser_click', 'browser_fill']:
                                try:
                                    snapshot_result = self.mcp_client.call_tool('browser_snapshot', {})
                                    if snapshot_result and isinstance(snapshot_result, dict):
                                        screenshot_path = snapshot_result.get('screenshot_path')
                                        if screenshot_path:
                                            step_info['screenshot_path'] = screenshot_path
                                            if progress_callback:
                                                self.logger.info(f"📸 Step {len(steps)} screenshot: {screenshot_path}")
                                                progress_callback('screenshot', {
                                                    'path': screenshot_path,
                                                    'url': snapshot_result.get('url', ''),
                                                    'step_number': len(steps)
                                                })
                                except Exception as screenshot_error:
                                    self.logger.warning(f"⚠️  Screenshot capture failed: {screenshot_error}")
                            
                            # Sanitize tool result to remove metadata fields that cause API errors
                            sanitized_content = self._sanitize_tool_result(result)
                            
                            self.conversation_history.append({
                                "role": "tool",
                                "tool_call_id": tool_call.id,
                                "content": sanitized_content
                            })
                            
                        except Exception as e:
                            error_msg = str(e)
                            
                            # Log action failure
                            if self.log_browser_actions:
                                self.logger.error("=" * 80)
                                self.logger.error(f"❌ Action '{tool_name}' FAILED")
                                self.logger.error(f"Error: {error_msg}")
                                self.logger.error("=" * 80)
                            
                            steps.append({
                                "tool": tool_name,
                                "arguments": tool_args,
                                "success": False,
                                "error": error_msg
                            })
                            
                            # Error messages are already plain strings, safe to use directly
                            self.conversation_history.append({
                                "role": "tool",
                                "tool_call_id": tool_call.id,
                                "content": f"Error: {error_msg}"
                            })
                else:
                    final_response = message.content or "Task completed"
                    
                    # Check for verification failures
                    verification_failure = self._check_verification_failure(final_response, steps, instruction)
                    if verification_failure:
                        self.logger.error("=" * 80)
                        self.logger.error("❌ VERIFICATION FAILED")
                        self.logger.error(f"Instruction: {verification_failure['instruction']}")
                        self.logger.error(f"Reason: {verification_failure['reason']}")
                        self.logger.error(f"Completed Steps: {verification_failure['completed_steps']}")
                        self.logger.error("=" * 80)
                        
                        # Return verification failure result
                        return {
                            "success": False,
                            "error": f"Verification failed: {verification_failure['reason']}",
                            "error_type": "VerificationError",
                            "verification_failed": True,
                            "verification_details": verification_failure,
                            "message": final_response,
                            "steps": steps,
                            "iterations": iteration
                        }
                    
                    # Log completion status
                    self.logger.info("=" * 80)
                    self.logger.info(f"✅ Execution Completed Successfully")
                    self.logger.info(f"Total Steps: {len(steps)}")
                    self.logger.info("=" * 80)
                    
                    # Collect screenshot paths from steps
                    screenshot_paths = [
                        step.get('screenshot_path') 
                        for step in steps 
                        if step.get('screenshot_path')
                    ]
                    
                    # Generate Python Playwright code using three-agent workflow
                    python_code = None
                    if self.generate_python_code:
                        try:
                            python_code = self._generate_python_code_from_execution(
                                instruction=instruction,
                                steps=steps,
                                final_message=final_response,
                                progress_callback=progress_callback
                            )
                        except Exception as gen_error:
                            self.logger.warning(f"⚠️ Python code generation failed: {gen_error}")
                            # Continue anyway - code generation is optional
                    
                    # Return execution results
                    return {
                        "success": True,
                        "message": final_response,
                        "steps": steps,
                        "iterations": iteration,
                        "screenshot_paths": screenshot_paths,
                        "playwright_code": python_code
                    }
                    
            except Exception as e:
                self.logger.error("=" * 80)
                self.logger.error(f"❌ Execution Failed — {type(e).__name__}")
                self.logger.error(f"Error: {str(e)}")
                self.logger.error("=" * 80)
                import traceback
                self.logger.debug(traceback.format_exc())
                
                return {
                    "success": False,
                    "error": str(e),
                    "steps": steps,
                    "iterations": iteration
                }
        
        # Max iterations reached
        self.logger.info("=" * 80)
        self.logger.info("❌ Execution Failed — Maximum iterations reached")
        self.logger.info(f"Completed Steps: {len(steps)}")
        self.logger.info("=" * 80)
        
        # Collect screenshot paths from steps
        screenshot_paths = [
            step.get('screenshot_path') 
            for step in steps 
            if step.get('screenshot_path')
        ]
        
        return {
            "success": False,
            "error": "Max iterations reached",
            "steps": steps,
            "iterations": iteration,
            "screenshot_paths": screenshot_paths
        }
    
    async def _execute_code_first_mode(self, instruction: str, progress_callback=None) -> Dict[str, Any]:
        """
        Execute using Code-First workflow: Plan → Generate → Execute → Heal
        
        This workflow ensures the generated code is validated and working:
        1. Planner Agent creates a structured plan
        2. Generator Agent creates Python Playwright code
        3. Code Executor runs the generated code
        4. If errors occur, Healer Agent fixes the code
        5. Loop back to step 3 (max 3 healing iterations)
        
        Args:
            instruction: User's natural language instruction
            progress_callback: Optional callback for progress updates
            
        Returns:
            Dictionary with execution results and working Python code
        """
        import asyncio
        
        try:
            self.logger.info("=" * 80)
            self.logger.info("🎯 CODE-FIRST WORKFLOW STARTING")
            self.logger.info("=" * 80)
            self.logger.info(f"Instruction: {instruction}")
            
            # Step 1: Planner Agent - Create automation plan
            if progress_callback:
                progress_callback('code_first_planning', {
                    'message': '🎭 Step 1/4: Creating automation plan...'
                })
            
            self.logger.info("🎭 Step 1: Running Planner Agent...")
            
            # Extract or infer start URL
            start_url = self._extract_url_from_instruction(instruction)
            if not start_url:
                start_url = "https://www.google.com"  # Default fallback
            
            plan_result = self.planner_agent.create_plan(
                goal=instruction,
                start_url=start_url,
                progress_callback=progress_callback
            )
            
            plan_yaml = plan_result.get('plan_yaml', '')
            
            if not plan_yaml:
                return {
                    "success": False,
                    "error": "Failed to create automation plan",
                    "message": "Planner Agent could not generate a valid plan",
                    "workflow": "code_first"
                }
            
            self.logger.info("✅ Plan created successfully")
            
            # Step 2: Generator Agent - Create Python code
            if progress_callback:
                progress_callback('code_first_generating', {
                    'message': '🎨 Step 2/4: Generating Python Playwright script...'
                })
            
            self.logger.info("🎨 Step 2: Running Generator Agent...")
            
            gen_result = self.generator_agent.generate_script(
                plan_yaml=plan_yaml,
                progress_callback=progress_callback
            )
            
            python_code = gen_result.get('python_code', '')
            
            if not python_code:
                return {
                    "success": False,
                    "error": "Failed to generate Python code",
                    "message": "Generator Agent could not create valid code",
                    "plan": plan_yaml,
                    "workflow": "code_first"
                }
            
            self.logger.info("✅ Python code generated successfully")
            
            # Step 3 & 4: Execute → Heal Loop (max 3 healing iterations)
            max_healing_iterations = 3
            healing_iteration = 0
            execution_successful = False
            final_code = python_code
            healing_history = []
            exec_result = {'success': False, 'output': '', 'error': 'No execution attempted'}
            
            while healing_iteration < max_healing_iterations and not execution_successful:
                healing_iteration += 1
                
                if healing_iteration == 1:
                    if progress_callback:
                        progress_callback('code_first_executing', {
                            'message': '▶️  Step 3/4: Executing generated script...'
                        })
                    self.logger.info("▶️  Step 3: Executing generated script...")
                else:
                    if progress_callback:
                        progress_callback('code_first_healing', {
                            'message': f'🔧 Step 4/{max_healing_iterations}: Healing iteration {healing_iteration-1}...'
                        })
                    self.logger.info(f"🔧 Healing iteration {healing_iteration-1}/{max_healing_iterations-1}...")
                
                # Execute the code
                exec_result = await self.code_executor.execute_script(
                    python_code=final_code,
                    progress_callback=progress_callback
                )
                
                if exec_result['success']:
                    execution_successful = True
                    self.logger.info("✅ Code executed successfully!")
                    
                    return {
                        "success": True,
                        "message": f"Automation completed successfully using Code-First workflow",
                        "playwright_code": final_code,
                        "output": exec_result.get('output', ''),
                        "execution_time": exec_result.get('execution_time', 0),
                        "healing_iterations": healing_iteration - 1,
                        "healing_history": healing_history,
                        "plan": plan_yaml,
                        "workflow": "code_first"
                    }
                else:
                    # Execution failed - use Healer to fix it
                    error_message = exec_result.get('error', 'Unknown error')
                    self.logger.error(f"❌ Execution failed: {error_message[:200]}")
                    
                    if healing_iteration >= max_healing_iterations:
                        # Max healing iterations reached
                        self.logger.error(f"❌ Max healing iterations ({max_healing_iterations}) reached")
                        break
                    
                    # Step 4: Healer Agent - Fix the code
                    if progress_callback:
                        progress_callback('code_first_healing', {
                            'message': f'🔧 Step 4: Healing script (attempt {healing_iteration}/{max_healing_iterations-1})...'
                        })
                    
                    self.logger.info(f"🔧 Step 4: Running Healer Agent (attempt {healing_iteration})...")
                    
                    heal_result = self.healer_agent.heal_script(
                        python_code=final_code,
                        error_message=error_message,
                        max_iterations=1,  # One fix per healing attempt
                        progress_callback=progress_callback
                    )
                    
                    if heal_result.get('success'):
                        healed_code = heal_result.get('healed_code', '')
                        if healed_code and healed_code != final_code:
                            final_code = healed_code
                            fixes_applied = heal_result.get('fixes_applied', '[]')
                            healing_history.append({
                                'iteration': healing_iteration,
                                'error': error_message[:300],
                                'fixes_applied': fixes_applied
                            })
                            self.logger.info("✅ Code healed, retrying execution...")
                        else:
                            self.logger.warning("⚠️  Healer returned no changes")
                            break
                    else:
                        self.logger.warning("⚠️  Healer could not fix the code")
                        break
            
            # All healing attempts exhausted
            return {
                "success": False,
                "error": "Code execution failed after healing attempts",
                "message": f"Failed to execute code after {healing_iteration} healing attempts",
                "playwright_code": final_code,
                "output": exec_result.get('output', ''),
                "last_error": exec_result.get('error', ''),
                "healing_iterations": healing_iteration,
                "healing_history": healing_history,
                "plan": plan_yaml,
                "workflow": "code_first"
            }
            
        except Exception as e:
            self.logger.error(f"❌ Code-First workflow error: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "message": "Code-First workflow encountered an unexpected error",
                "workflow": "code_first"
            }
    
    def _extract_url_from_instruction(self, instruction: str) -> Optional[str]:
        """
        Extract URL from instruction text
        
        Args:
            instruction: User instruction
            
        Returns:
            Extracted URL or None
        """
        import re
        
        # Look for URLs in the instruction
        url_pattern = r'https?://[^\s]+'
        matches = re.findall(url_pattern, instruction)
        
        if matches:
            return matches[0]
        
        # Look for common domain references
        if 'google' in instruction.lower():
            return 'https://www.google.com'
        elif 'github' in instruction.lower():
            return 'https://github.com'
        elif 'example.com' in instruction.lower():
            return 'https://example.com'
        
        return None
    
    def _sanitize_tool_result(self, result: Any) -> str:
        """
        Sanitize tool result to remove metadata fields that the API gateway doesn't expect.
        
        The API expects a simple string output, not complex nested objects with metadata.
        This prevents 400 Bad Request errors caused by malformed JSON in tool outputs.
        
        Args:
            result: Raw tool result from MCP client
            
        Returns:
            Sanitized string representation suitable for API gateway
        """
        if result is None:
            return "null"
        
        # If result is a string, return it directly
        if isinstance(result, str):
            return result
        
        # If result is a dict, extract meaningful content and remove metadata fields
        if isinstance(result, dict):
            # Remove metadata fields that cause API errors
            sanitized = {}
            metadata_fields = {'message', 'id', '_metadata', '__meta__'}
            
            for key, value in result.items():
                # Skip metadata fields
                if key in metadata_fields:
                    continue
                # Include all other fields
                sanitized[key] = value
            
            # If we removed everything, return a simple success message
            if not sanitized:
                return json.dumps({"status": "success"})
            
            # Return clean JSON without metadata
            return json.dumps(sanitized, indent=2)
        
        # For other types, convert to string
        return str(result)
    
    def _format_action_description(self, tool_name: str, tool_args: Dict[str, Any]) -> str:
        """
        Format a concise action description for logging
        
        Args:
            tool_name: Name of the tool/action
            tool_args: Tool arguments
            
        Returns:
            Concise human-readable description
        """
        # Map tool names to user-friendly action names
        action_map = {
            'browser_navigate': 'Navigate',
            'browser_click': 'Click',
            'browser_fill': 'Fill',
            'browser_snapshot': 'Snapshot',
            'browser_scroll': 'Scroll',
            'browser_hover': 'Hover',
            'browser_select': 'Select',
            'browser_extract': 'Extract',
            'browser_wait': 'Wait'
        }
        
        action = action_map.get(tool_name, tool_name.replace('browser_', '').title())
        
        # Format based on specific action types
        if tool_name == 'browser_navigate':
            url = tool_args.get('url', '')
            return f"{action} to {url}"
        elif tool_name == 'browser_click':
            ref = tool_args.get('element_ref', tool_args.get('selector', ''))
            return f"{action} element {ref}"
        elif tool_name == 'browser_fill':
            ref = tool_args.get('element_ref', tool_args.get('selector', ''))
            value = tool_args.get('value', '')
            # Truncate long values
            value_display = value[:50] + '...' if len(value) > 50 else value
            return f"{action} '{value_display}' in {ref}"
        elif tool_name == 'browser_snapshot':
            return f"{action} page state"
        else:
            # Generic format for other actions
            return f"{action} - {str(tool_args)[:80]}"
    
    def reset_conversation(self):
        """Reset the conversation history"""
        self.conversation_history = []
    
    def _generate_python_code_from_execution(
        self,
        instruction: str,
        steps: List[Dict],
        final_message: str,
        progress_callback=None
    ) -> str:
        """
        Generate standalone Python Playwright code from successful execution
        Uses the three-agent workflow: Plan → Generate → (Heal if needed)
        
        Args:
            instruction: Original automation instruction
            steps: List of executed steps
            final_message: Final completion message
            progress_callback: Optional callback for progress updates
            
        Returns:
            Generated Python Playwright code as string
        """
        try:
            self.logger.info("🎨 Starting Python code generation with three-agent workflow...")
            
            # Extract start URL from steps
            start_url = self._extract_url_from_steps(steps, instruction)
            
            if not start_url:
                self.logger.warning("⚠️ Could not determine start URL, using simple generation")
                return self._generate_simple_python_code(instruction, steps)
            
            # Step 1: Use Planner Agent to create structured plan
            if progress_callback:
                progress_callback('code_gen_planning', {
                    'message': '🎭 Creating automation plan...'
                })
            
            self.logger.info("🎭 Step 1/2: Running Planner Agent...")
            plan_result = self.planner_agent.create_plan(
                goal=instruction,
                start_url=start_url,
                progress_callback=progress_callback
            )
            
            plan_yaml = plan_result.get('plan_yaml', '')
            
            if not plan_yaml:
                self.logger.warning("⚠️ Planner did not generate a plan, using simple generation")
                return self._generate_simple_python_code(instruction, steps)
            
            # Step 2: Use Generator Agent to create Python code
            if progress_callback:
                progress_callback('code_gen_generating', {
                    'message': '🎨 Generating Python Playwright script...'
                })
            
            self.logger.info("🎨 Step 2/2: Running Generator Agent...")
            gen_result = self.generator_agent.generate_script(
                plan_yaml=plan_yaml,
                progress_callback=progress_callback
            )
            
            python_code = gen_result.get('python_code', '')
            
            if not python_code:
                self.logger.warning("⚠️ Generator did not produce code, using simple generation")
                return self._generate_simple_python_code(instruction, steps)
            
            self.logger.info("✅ Python code generation complete!")
            
            # Note: Healer Agent would be called here if we detected execution errors
            # For now, we return the generated code directly
            
            return python_code
            
        except Exception as e:
            self.logger.error(f"❌ Python code generation failed: {e}", exc_info=True)
            # Fallback to simple generation
            return self._generate_simple_python_code(instruction, steps)
    
    def _extract_url_from_steps(self, steps: List[Dict], instruction: str) -> Optional[str]:
        """Extract starting URL from execution steps or instruction"""
        # Look for navigation steps
        for step in steps:
            if step.get('tool') == 'browser_navigate':
                args = step.get('arguments', {})
                if isinstance(args, dict) and 'url' in args:
                    return args['url']
        
        # Try to extract URL from instruction
        import re
        url_pattern = r'https?://[^\s<>"]+'
        matches = re.findall(url_pattern, instruction)
        if matches:
            return matches[0]
        
        # Default to a placeholder
        return "https://example.com"
    
    def _generate_simple_python_code(self, instruction: str, steps: List[Dict]) -> str:
        """
        Generate simple Python code as fallback when three-agent workflow fails
        
        Args:
            instruction: Original instruction
            steps: Executed steps
            
        Returns:
            Basic Python Playwright script
        """
        # Extract URL
        start_url = self._extract_url_from_steps(steps, instruction)
        
        # Build basic script
        code = f'''"""
Playwright Python Automation Script
Generated from: {instruction}
"""
import asyncio
import logging
from playwright.async_api import async_playwright

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    """Main automation function"""
    async with async_playwright() as p:
        # Launch browser
        logger.info("Launching browser...")
        browser = await p.chromium.launch(headless=False)
        
        try:
            # Create context
            context = await browser.new_context(
                viewport={{'width': 1280, 'height': 720}}
            )
            page = await context.new_page()
            page.set_default_timeout(30000)
            
            logger.info("Starting automation...")
            
            # Navigate to starting URL
            await page.goto("{start_url}", wait_until="networkidle")
            logger.info(f"Navigated to {{page.url}}")
            
            # TODO: Add automation steps based on: {instruction}
            # This is a basic template - customize based on your needs
            
            logger.info("✅ Automation completed successfully")
            
        except Exception as e:
            logger.error(f"❌ Automation failed: {{e}}")
            raise
        finally:
            await browser.close()
            logger.info("Browser closed")


if __name__ == "__main__":
    asyncio.run(main())
'''
        return code
