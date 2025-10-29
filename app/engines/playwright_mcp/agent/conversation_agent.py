"""
OpenAI-powered Browser Agent
Interprets natural language instructions and executes browser actions
Uses direct execution mode for browser automation tasks
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
from app.engines.playwright_mcp.file_manager import AgentFileManager

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
        
        # Initialize File Manager for file-based workflow
        self.file_manager = AgentFileManager(workspace_root)
        self.file_manager.initialize_directories()
        
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
                "content": """You are an efficient browser automation assistant. 
Complete the user's task quickly and accurately using the minimum necessary steps.

Instructions:
1. Break down the task into the essential browser automation steps
2. Navigate to websites, interact with elements, and extract data as needed
3. When you see page snapshots in YAML format, use element references like [ref=e1], [ref=e2] for browser_click and browser_fill
4. Complete the task efficiently - avoid unnecessary snapshots or redundant actions
5. Once the task is complete, respond with your completion message (no more tool calls)

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
                            
                            self.conversation_history.append({
                                "role": "tool",
                                "tool_call_id": tool_call.id,
                                "content": json.dumps(result, indent=2)
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
                    
                    # Return execution results
                    return {
                        "success": True,
                        "message": final_response,
                        "steps": steps,
                        "iterations": iteration
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
        return {
            "success": False,
            "error": "Max iterations reached",
            "steps": steps,
            "iterations": iteration
        }
    
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
