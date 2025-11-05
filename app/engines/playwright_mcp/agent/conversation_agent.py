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
        self.healer_agent = HealerAgent(llm_client=self.client, model=self.model)
        
        # Disable automatic code generation to avoid duplicate execution
        # Code generation can be enabled explicitly when needed
        self.generate_python_code = False
        
        
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
        Execute a natural language instruction using direct mode
        
        Args:
            instruction: User's natural language instruction
            mode: Must be "direct" (other modes have been removed)
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
                "content": """You are an intelligent browser automation assistant that follows a structured OBSERVE→REASON→ACT→VERIFY workflow.

═══════════════════════════════════════════════════════════════════════════════
🎯 CORE WORKFLOW (MANDATORY)
═══════════════════════════════════════════════════════════════════════════════

For EVERY task, you MUST follow this cycle:

1. **OBSERVE** - Gather context BEFORE acting
   - If task specifies a URL: browser_navigate to it, THEN immediately browser_snapshot
   - If task doesn't specify URL: Start with browser_snapshot to see current page
   - You must have a snapshot showing elements before any interaction (clicks, fills, etc.)
   - Use browser_snapshot to inspect page structure and identify available elements

2. **REASON** - Think before you act
   - State your THOUGHT: explain your plan for the next 1-3 steps
   - Identify which elements you'll interact with (using [ref=eN] from snapshots)
   - Anticipate what should happen after your action

3. **ACT** - Execute ONE focused action
   - Use the appropriate tool based on your reasoning
   - Reference elements from snapshots using [ref=eN] notation
   - Wait for action to complete before next OBSERVE

4. **VERIFY** - Confirm the action succeeded
   - After critical actions, take another snapshot to verify state changed as expected
   - For verification tasks (with keywords: verify, check, ensure, validate, assert, confirm), 
     you MUST actively check the condition using browser_snapshot or browser_text
   - Report clear success/failure: "Verification passed: [what was confirmed]" OR "Verification failed: [specific reason]"

═══════════════════════════════════════════════════════════════════════════════
🛠️ TOOL SELECTION GUIDE
═══════════════════════════════════════════════════════════════════════════════

Use this decision table to choose the right tool:

| WHEN TO USE                           | TOOL                    | EXAMPLE                                    |
|---------------------------------------|-------------------------|---------------------------------------------|
| Starting task, going to URL           | browser_navigate        | browser_navigate(url="https://example.com")|
| Need to see page structure/elements   | browser_snapshot        | browser_snapshot()                         |
| Click button/link/element             | browser_click           | browser_click(element_ref="[ref=e3]")      |
| Type into input field                 | browser_fill            | browser_fill(element_ref="[ref=e5]", value="text") |
| Select from native <select> dropdown  | browser_select          | browser_select(element_ref="[ref=e2]", value="option1") |
| Extract visible text from element     | browser_text            | browser_text(element_ref="[ref=e7]")       |
| Get element attributes (href, src)    | browser_attribute       | browser_attribute(element_ref="[ref=e4]", name="href") |
| Scroll page or element                | browser_scroll          | browser_scroll(direction="down", amount=500)|
| Hover over element                    | browser_hover           | browser_hover(element_ref="[ref=e6]")      |
| Press keyboard key (Enter, Tab, etc)  | browser_press           | browser_press(key="Enter")                 |
| Wait for page to load/settle          | browser_wait            | browser_wait(milliseconds=1000)            |
| Take screenshot (debugging only)      | browser_screenshot      | browser_screenshot()                       |

═══════════════════════════════════════════════════════════════════════════════
🔍 ELEMENT REFERENCES
═══════════════════════════════════════════════════════════════════════════════

When you call browser_snapshot, you'll receive YAML with elements like:
```
elements:
  - ref: e1
    tag: button
    text: "Submit"
    aria_label: "Submit form"
```

ALWAYS use the [ref=eN] notation when calling action tools:
✅ CORRECT: browser_click(element_ref="[ref=e1]")
❌ WRONG: browser_click(element_ref="Submit button")
❌ WRONG: browser_click(element_ref="e1")

═══════════════════════════════════════════════════════════════════════════════
⚙️ DROPDOWN HANDLING (Advanced)
═══════════════════════════════════════════════════════════════════════════════

**Native HTML <select>**: Use browser_select directly with value/label/index
**Custom JS dropdowns** (Material-UI, Ant Design, etc):
   1. browser_click to open → 2. browser_wait briefly → 3. browser_snapshot to see options → 4. browser_click on option [ref]
**Dropdown with search**: browser_click to open → browser_fill to search → browser_snapshot → browser_click on result
**Long lists**: Use browser_scroll within dropdown if needed, or prefer search/filter
**Multi-select**: Click each option, don't close dropdown until all selected

═══════════════════════════════════════════════════════════════════════════════
🚨 ERROR HANDLING & RECOVERY
═══════════════════════════════════════════════════════════════════════════════

If a tool call FAILS or returns an error:
1. Take a browser_snapshot to reassess the current page state
2. STATE YOUR THOUGHT about what went wrong and your recovery plan
3. Try an alternative approach (different element, different tool, wait first)
4. If element not found: browser_scroll to find it, or browser_wait for it to load
5. If stuck after 3 attempts: clearly report the failure with specific reason

Common recoveries:
- "Element not found" → Take snapshot, verify element exists, try different ref
- "Click failed" → Try browser_hover first, then browser_click
- "Page didn't load" → Use browser_wait, then browser_snapshot to confirm
- "Dropdown not opening" → Try browser_hover before browser_click
- "Network timeout" → browser_wait longer, then retry navigation

═══════════════════════════════════════════════════════════════════════════════
✅ TASK COMPLETION CRITERIA
═══════════════════════════════════════════════════════════════════════════════

Before declaring task complete:
1. Have you completed ALL steps requested by the user?
2. Have you VERIFIED the final state (if verification keywords present)?
3. Have you confirmed success with browser_snapshot or browser_text?

Only then respond with your completion message (no more tool calls).

═══════════════════════════════════════════════════════════════════════════════
📋 EXAMPLE WORKFLOW
═══════════════════════════════════════════════════════════════════════════════

User: "Go to example.com and search for 'playwright'"

THOUGHT: I need to navigate to example.com, observe the page structure, find the search box, fill it, and submit.

[Tool: browser_navigate(url="https://example.com")]
[Tool: browser_snapshot()]

THOUGHT: I can see element [ref=e5] is a search input. I'll fill it with 'playwright' and then look for a search button.

[Tool: browser_fill(element_ref="[ref=e5]", value="playwright")]
[Tool: browser_snapshot()]

THOUGHT: Element [ref=e8] is the search button. I'll click it and verify results loaded.

[Tool: browser_click(element_ref="[ref=e8]")]
[Tool: browser_wait(milliseconds=1500)]
[Tool: browser_snapshot()]

THOUGHT: Search results are now visible on the page. Task complete.

Response: "Successfully searched for 'playwright' on example.com. Search results are now displayed."

═══════════════════════════════════════════════════════════════════════════════
Remember: OBSERVE→REASON→ACT→VERIFY. Always observe first, reason about your plan, act decisively, then verify the result.
═══════════════════════════════════════════════════════════════════════════════"""
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
