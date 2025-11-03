"""
Planner Agent
Explores the application and generates structured automation plans with validated strict-mode locators
"""
import logging
import yaml
import json
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class PlannerAgent:
    """
    Planner Agent that explores applications and creates structured automation plans
    Generates YAML plans with validated locators and step-by-step actions
    """
    
    def __init__(self, mcp_client, llm_client, locator_engine):
        """
        Initialize Planner Agent
        
        Args:
            mcp_client: MCP client for browser interactions
            llm_client: LLM client for intelligent planning
            locator_engine: StrictModeLocatorEngine instance
        """
        self.mcp_client = mcp_client
        self.llm_client = llm_client
        self.locator_engine = locator_engine
        self.conversation_history = []
    
    def create_plan(self, goal: str, start_url: str, progress_callback=None) -> Dict[str, Any]:
        """
        Create an automation plan by exploring the application
        
        Args:
            goal: Natural language automation goal
            start_url: Starting URL for exploration
            progress_callback: Optional callback for progress updates
            
        Returns:
            Dictionary containing plan_yaml, validated_locators, and metadata
        """
        try:
            if progress_callback:
                progress_callback('planner_init', {
                    'message': '🎭 Planner Agent: Analyzing automation goal...',
                    'goal': goal,
                    'start_url': start_url
                })
            
            logger.info(f"🎭 Planner Agent: Creating plan for '{goal}' at {start_url}")
            
            # Initialize conversation with system prompt
            self.conversation_history = [
                {
                    "role": "system",
                    "content": self._get_planner_system_prompt()
                },
                {
                    "role": "user",
                    "content": f"""Create an automation plan:
Goal: {goal}
Start URL: {start_url}

Navigate to the URL, explore the page, identify elements, then generate a YAML plan with goal, start_url, and steps."""
                }
            ]
            
            # Get available MCP tools
            tools = self.mcp_client.get_tools_schema()
            
            if progress_callback:
                progress_callback('planner_explore', {
                    'message': '🎭 Planner Agent: Exploring application and identifying elements...'
                })
            
            # Execute planning conversation loop
            steps_taken = []
            max_iterations = 15
            iteration = 0
            
            while iteration < max_iterations:
                iteration += 1
                
                # Get LLM response with tool access
                response = self.llm_client.chat.completions.create(
                    model="gpt-4o",
                    max_tokens=4096,
                    tools=tools,
                    messages=self.conversation_history
                )
                
                # Get assistant message from OpenAI response
                assistant_message = response.choices[0].message
                
                # Add assistant response to conversation (following OpenAI format)
                assistant_entry = {
                    "role": "assistant",
                    "content": assistant_message.content if assistant_message.content else ""
                }
                # Only add tool_calls if they exist (don't include None)
                if assistant_message.tool_calls:
                    assistant_entry["tool_calls"] = assistant_message.tool_calls
                
                self.conversation_history.append(assistant_entry)
                
                # Check if we have a final plan
                has_tool_calls = assistant_message.tool_calls is not None and len(assistant_message.tool_calls) > 0
                
                if not has_tool_calls:
                    # Extract the plan from the response
                    text_content = assistant_message.content if assistant_message.content else ""
                    
                    if progress_callback:
                        progress_callback('planner_complete', {
                            'message': '🎭 Planner Agent: Plan generation complete!'
                        })
                    
                    # Parse the YAML plan
                    plan_data = self._extract_yaml_plan(text_content)
                    
                    if plan_data:
                        logger.info("✅ Planner Agent: Successfully created automation plan")
                        return {
                            'plan_yaml': yaml.dump(plan_data, default_flow_style=False),
                            'validated_locators': json.dumps(self._extract_locators_from_plan(plan_data)),
                            'metadata': json.dumps({
                                'iterations': iteration,
                                'steps_explored': len(steps_taken),
                                'created_at': datetime.utcnow().isoformat()
                            })
                        }
                    else:
                        # No valid YAML found, treat as completion message
                        logger.warning("No YAML plan found in response, creating basic plan")
                        basic_plan = self._create_basic_plan(goal, start_url, steps_taken)
                        return {
                            'plan_yaml': yaml.dump(basic_plan, default_flow_style=False),
                            'validated_locators': json.dumps({}),
                            'metadata': json.dumps({
                                'iterations': iteration,
                                'fallback': True
                            })
                        }
                
                # Execute tool calls
                if has_tool_calls:
                    tool_results = []
                    for tool_call in assistant_message.tool_calls:
                        tool_name = tool_call.function.name
                        tool_input = json.loads(tool_call.function.arguments)
                        
                        logger.info(f"🔧 Planner executing tool: {tool_name}")
                        steps_taken.append({
                            'tool': tool_name,
                            'input': tool_input
                        })
                        
                        if progress_callback:
                            progress_callback('planner_action', {
                                'message': f'🎭 Planner: Executing {tool_name}...',
                                'tool': tool_name
                            })
                        
                        # Execute the tool via MCP
                        result = self.mcp_client.call_tool(tool_name, tool_input)
                        
                        tool_results.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": json.dumps(result) if not isinstance(result, str) else result
                        })
                    
                    # Add tool results to conversation
                    if tool_results:
                        self.conversation_history.extend(tool_results)
            
            # Max iterations reached
            logger.warning(f"⚠️ Planner Agent reached max iterations ({max_iterations})")
            basic_plan = self._create_basic_plan(goal, start_url, steps_taken)
            
            return {
                'plan_yaml': yaml.dump(basic_plan, default_flow_style=False),
                'validated_locators': json.dumps({}),
                'metadata': json.dumps({
                    'iterations': max_iterations,
                    'timeout': True
                })
            }
            
        except Exception as e:
            logger.error(f"❌ Planner Agent error: {e}", exc_info=True)
            raise
    
    def _get_planner_system_prompt(self) -> str:
        """Get system prompt for the planner agent"""
        return """Automation planner: explore pages, identify elements, create YAML plans.

1. Navigate & snapshot to understand UI
2. Validate locators (test-id, ARIA, text, selectors)
3. Generate YAML:
goal: "task"
start_url: "url"
steps:
  - step_number: N
    action: navigate|click|fill|press|select|wait|screenshot
    description: "step info"
    target_url: "url" (navigate only)
    element: {locator_strategy: "type", locator: "selector", text: "label"} (interactions)
    value: "input" (fill/select)

After exploration, output complete YAML plan."""
    
    def _extract_text_from_response(self, response) -> str:
        """Extract text content from LLM response"""
        text_parts = []
        for block in response.content:
            if block.type == "text":
                text_parts.append(block.text)
        return '\n'.join(text_parts)
    
    def _extract_yaml_plan(self, text: str) -> Optional[Dict]:
        """Extract YAML plan from text response"""
        try:
            # Look for YAML code blocks
            yaml_pattern = r'```(?:yaml|yml)?\s*\n(.*?)\n```'
            import re
            matches = re.findall(yaml_pattern, text, re.DOTALL)
            
            if matches:
                # Try to parse the first YAML block
                plan = yaml.safe_load(matches[0])
                if isinstance(plan, dict) and 'goal' in plan:
                    return plan
            
            # Try parsing the entire text as YAML
            plan = yaml.safe_load(text)
            if isinstance(plan, dict) and 'goal' in plan:
                return plan
                
        except Exception as e:
            logger.debug(f"Could not extract YAML plan: {e}")
        
        return None
    
    def _extract_locators_from_plan(self, plan: Dict) -> Dict[str, Any]:
        """Extract all validated locators from the plan"""
        locators = {}
        
        steps = plan.get('steps', [])
        for step in steps:
            if 'element' in step:
                step_num = step.get('step_number', 'unknown')
                locators[f"step_{step_num}"] = step['element']
        
        return locators
    
    def _create_basic_plan(self, goal: str, start_url: str, steps_taken: List[Dict]) -> Dict:
        """Create a basic fallback plan"""
        return {
            'goal': goal,
            'start_url': start_url,
            'steps': [
                {
                    'step_number': 1,
                    'action': 'navigate',
                    'description': f'Navigate to {start_url}',
                    'target_url': start_url
                }
            ],
            'metadata': {
                'fallback': True,
                'exploration_steps': len(steps_taken)
            }
        }
