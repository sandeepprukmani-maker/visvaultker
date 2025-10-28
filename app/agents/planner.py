"""
Planner Agent - Explores app and creates execution plan using real engine intelligence
Based on Playwright's pwt-planner.agent.md
"""
import logging
import json
import re
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


class PlannerAgent:
    """
    Expert web test planner that explores applications and creates execution plans.
    
    Uses the engine's browser and LLM capabilities to:
    1. Navigate and explore the target application
    2. Analyze user flows and identify critical paths
    3. Design comprehensive scenarios with detailed steps
    4. Create structured plans optimized for code generation
    """
    
    PLANNER_SYSTEM_PROMPT = """You are an expert web automation planner with extensive experience in quality assurance, 
user experience testing, and automation design.

Your task is to analyze a browser automation request and create a DETAILED, STEP-BY-STEP execution plan.

**Critical Requirements**:
1. Break down the automation into atomic, sequential steps
2. For EACH step, identify the specific element to interact with
3. Use descriptive element selectors (button names, input labels, link text, etc.)
4. Include expected outcomes and verification points
5. Focus on creating ONE happy path scenario (the most common use case)
6. Make steps specific enough for code generation

**Output Format** (JSON):
{{
  "scenario_name": "Brief name for the automation",
  "description": "What this automation accomplishes",
  "url": "Starting URL if known",
  "steps": [
    {{
      "step_number": 1,
      "action": "navigate|click|fill|select|wait|verify",
      "target": "Specific element description or URL",
      "value": "Value to enter (for fill/select actions)",
      "expected_result": "What should happen after this step",
      "locator_strategy": "role|text|label|placeholder|testid",
      "timeout": 10000,
      "critical": true
    }}
  ]
}}

**Best Practices for Steps**:
- Use role-based locators for buttons (most reliable)
- Use label-based locators for form inputs
- Add wait steps after navigation and form submissions
- Set timeout to 10000ms for most actions, 30000ms for slow operations
- Mark critical steps (login, payment) with "critical": true

**Example for "Login to Gmail"**:
{{
  "scenario_name": "Gmail Login",
  "description": "Authenticate user into Gmail account",
  "url": "https://gmail.com",
  "steps": [
    {{
      "step_number": 1,
      "action": "navigate",
      "target": "https://gmail.com",
      "expected_result": "Gmail login page loads",
      "locator_strategy": "url"
    }},
    {{
      "step_number": 2,
      "action": "fill",
      "target": "Email or phone input field",
      "value": "user@gmail.com",
      "expected_result": "Email is entered",
      "locator_strategy": "label"
    }},
    {{
      "step_number": 3,
      "action": "click",
      "target": "Next button",
      "expected_result": "Password page appears",
      "locator_strategy": "role"
    }},
    {{
      "step_number": 4,
      "action": "fill",
      "target": "Password input field",
      "value": "password123",
      "expected_result": "Password is entered",
      "locator_strategy": "label"
    }},
    {{
      "step_number": 5,
      "action": "click",
      "target": "Next button",
      "expected_result": "User is logged in to inbox",
      "locator_strategy": "role"
    }}
  ]
}}

Now, create a plan for this automation task:
{instruction}

Return ONLY valid JSON, no markdown formatting or explanations."""
    
    def __init__(self, engine):
        """
        Initialize Planner Agent
        
        Args:
            engine: The browser automation engine (Playwright MCP or Browser-Use)
        """
        self.engine = engine
        
    async def create_plan(self, instruction: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Create an execution plan for the given instruction using LLM intelligence
        
        Args:
            instruction: Natural language task description
            context: Optional context (URL, existing state, etc.)
            
        Returns:
            Structured plan as a dictionary
        """
        logger.info(f"🎭 Planner Agent: Creating intelligent plan for '{instruction[:50]}...'")
        
        context = context or {}
        
        # Build the planning prompt with context
        planning_prompt = self.PLANNER_SYSTEM_PROMPT.format(instruction=instruction)
        
        if context.get('url'):
            planning_prompt += f"\n\nTarget URL: {context['url']}"
        
        try:
            # Use the engine's LLM to create the plan
            plan_result = await self._generate_plan_with_llm(planning_prompt, instruction, context)
            
            logger.info(f"✅ Intelligent plan created with {len(plan_result.get('steps', []))} steps")
            return plan_result
            
        except Exception as e:
            logger.error(f"❌ Planner failed: {e}", exc_info=True)
            # Fallback: create basic plan from instruction
            return self._create_fallback_plan(instruction, context)
    
    async def _generate_plan_with_llm(self, prompt: str, instruction: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Use the engine's LLM to generate an intelligent plan
        
        Args:
            prompt: The planning prompt
            instruction: Original instruction
            context: Execution context
            
        Returns:
            Structured plan from LLM
        """
        # Check if engine has LLM capabilities
        if hasattr(self.engine, 'llm') or hasattr(self.engine, 'chat_model'):
            logger.info("   Using engine's LLM for intelligent planning")
            
            # Get LLM instance
            llm = getattr(self.engine, 'llm', None) or getattr(self.engine, 'chat_model', None)
            
            if llm:
                try:
                    # Call the LLM to generate plan
                    if hasattr(llm, 'apredict') or hasattr(llm, 'ainvoke'):
                        # LangChain-style LLM
                        method = getattr(llm, 'apredict', None) or getattr(llm, 'ainvoke', None)
                        if method:
                            response = await method(prompt)
                        else:
                            raise ValueError("No valid LLM method found")
                        
                        # Extract JSON from response
                        if isinstance(response, str):
                            plan_json = self._extract_json_from_response(response)
                        else:
                            plan_json = response
                        
                        # Validate and return
                        if isinstance(plan_json, dict) and 'steps' in plan_json:
                            return plan_json
                    
                except Exception as e:
                    logger.warning(f"   LLM planning failed: {e}, falling back to heuristic planning")
        
        # Fallback to intelligent parsing
        logger.info("   Using heuristic planning (no LLM available)")
        return self._intelligent_parse_instruction(instruction, context)
    
    def _extract_json_from_response(self, response: str) -> Dict[str, Any]:
        """Extract JSON from LLM response that might include markdown"""
        # Remove markdown code blocks
        response = response.replace('```json', '').replace('```', '').strip()
        
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            # Try to find JSON in the response
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group(0))
                except:
                    pass
            raise ValueError("Could not extract valid JSON from response")
    
    def _intelligent_parse_instruction(self, instruction: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Intelligently parse instruction into a structured plan using heuristics
        
        Args:
            instruction: Natural language task
            context: Context information
            
        Returns:
            Structured plan
        """
        steps = []
        lower_instruction = instruction.lower()
        
        # Extract URL if present in instruction or context
        url = context.get('url')
        if not url:
            url_pattern = r'https?://[^\s]+'
            url_match = re.search(url_pattern, instruction)
            if url_match:
                url = url_match.group(0)
        
        # Add navigation step if URL available
        if url:
            steps.append({
                "step_number": len(steps) + 1,
                "action": "navigate",
                "target": url,
                "expected_result": "Page loads successfully",
                "locator_strategy": "url"
            })
        
        # Pattern-based step extraction
        patterns = [
            # Login patterns
            (r'login|sign in|authenticate', self._create_login_steps),
            # Search patterns
            (r'search|find|look for', self._create_search_steps),
            # Drag and drop patterns
            (r'drag.*drop|drag.*to|move.*to', self._create_drag_drop_steps),
            # Upload patterns
            (r'upload|attach.*file|choose.*file', self._create_upload_steps),
            # Assertion/verify patterns
            (r'assert|verify|check|validate|expect', self._create_assertion_steps),
            # Screenshot patterns
            (r'screenshot|capture|snap', self._create_screenshot_steps),
            # Scroll patterns
            (r'scroll', self._create_scroll_steps),
            # Hover patterns
            (r'hover|mouse over', self._create_hover_steps),
            # Click patterns
            (r'click|press|tap', self._create_click_steps),
            # Form fill patterns
            (r'fill|enter|type|input', self._create_fill_steps),
            # Download patterns
            (r'download|save', self._create_download_steps),
        ]
        
        for pattern, step_creator in patterns:
            if re.search(pattern, lower_instruction):
                created_steps = step_creator(instruction, len(steps) + 1)
                steps.extend(created_steps)
                break
        
        # If no pattern matched, create generic steps
        if len(steps) <= 1:
            steps.append({
                "step_number": len(steps) + 1,
                "action": "execute",
                "target": "Perform automation task",
                "expected_result": "Task completes successfully",
                "locator_strategy": "auto"
            })
        
        return {
            "scenario_name": instruction[:60] + ("..." if len(instruction) > 60 else ""),
            "description": instruction,
            "url": url,
            "steps": steps
        }
    
    def _create_login_steps(self, instruction: str, start_num: int) -> List[Dict[str, Any]]:
        """Create steps for login scenario"""
        return [
            {
                "step_number": start_num,
                "action": "fill",
                "target": "Email or username input field",
                "value": "user@example.com",
                "expected_result": "Username is entered",
                "locator_strategy": "label"
            },
            {
                "step_number": start_num + 1,
                "action": "fill",
                "target": "Password input field",
                "value": "password123",
                "expected_result": "Password is entered",
                "locator_strategy": "label"
            },
            {
                "step_number": start_num + 2,
                "action": "click",
                "target": "Login or Sign In button",
                "expected_result": "User is logged in",
                "locator_strategy": "role"
            }
        ]
    
    def _create_search_steps(self, instruction: str, start_num: int) -> List[Dict[str, Any]]:
        """Create steps for search scenario"""
        # Extract search term if possible
        import re
        search_match = re.search(r'search for ["\']?([^"\']+)["\']?', instruction, re.IGNORECASE)
        search_term = search_match.group(1) if search_match else "search query"
        
        return [
            {
                "step_number": start_num,
                "action": "fill",
                "target": "Search input field",
                "value": search_term,
                "expected_result": "Search term is entered",
                "locator_strategy": "placeholder"
            },
            {
                "step_number": start_num + 1,
                "action": "click",
                "target": "Search button or press Enter",
                "expected_result": "Search results appear",
                "locator_strategy": "role"
            }
        ]
    
    def _create_click_steps(self, instruction: str, start_num: int) -> List[Dict[str, Any]]:
        """Create steps for click scenario"""
        return [
            {
                "step_number": start_num,
                "action": "click",
                "target": "Target element from instruction",
                "expected_result": "Element is clicked",
                "locator_strategy": "text"
            }
        ]
    
    def _create_fill_steps(self, instruction: str, start_num: int) -> List[Dict[str, Any]]:
        """Create steps for form fill scenario"""
        return [
            {
                "step_number": start_num,
                "action": "fill",
                "target": "Input field",
                "value": "value from instruction",
                "expected_result": "Field is filled",
                "locator_strategy": "label"
            }
        ]
    
    def _create_download_steps(self, instruction: str, start_num: int) -> List[Dict[str, Any]]:
        """Create steps for download scenario"""
        return [
            {
                "step_number": start_num,
                "action": "click",
                "target": "Download button or link",
                "expected_result": "Download starts",
                "locator_strategy": "role"
            },
            {
                "step_number": start_num + 1,
                "action": "wait",
                "target": "Download to complete",
                "expected_result": "File is downloaded",
                "locator_strategy": "auto"
            }
        ]
    
    def _create_drag_drop_steps(self, instruction: str, start_num: int) -> List[Dict[str, Any]]:
        """Create steps for drag and drop scenario"""
        return [
            {
                "step_number": start_num,
                "action": "drag_drop",
                "target": "Source element to drag",
                "value": "Target element to drop",
                "expected_result": "Element is dragged and dropped",
                "locator_strategy": "text"
            }
        ]
    
    def _create_upload_steps(self, instruction: str, start_num: int) -> List[Dict[str, Any]]:
        """Create steps for file upload scenario"""
        return [
            {
                "step_number": start_num,
                "action": "upload",
                "target": "File input field",
                "value": "path/to/file",
                "expected_result": "File is uploaded",
                "locator_strategy": "label"
            }
        ]
    
    def _create_assertion_steps(self, instruction: str, start_num: int) -> List[Dict[str, Any]]:
        """Create steps for assertion/verification scenario"""
        return [
            {
                "step_number": start_num,
                "action": "verify",
                "target": "Element or text to verify",
                "expected_result": "Element is visible and matches expectation",
                "locator_strategy": "text"
            }
        ]
    
    def _create_screenshot_steps(self, instruction: str, start_num: int) -> List[Dict[str, Any]]:
        """Create steps for screenshot scenario"""
        return [
            {
                "step_number": start_num,
                "action": "screenshot",
                "target": "Page or element to capture",
                "expected_result": "Screenshot is saved",
                "locator_strategy": "auto"
            }
        ]
    
    def _create_scroll_steps(self, instruction: str, start_num: int) -> List[Dict[str, Any]]:
        """Create steps for scroll scenario"""
        return [
            {
                "step_number": start_num,
                "action": "scroll",
                "target": "Element to scroll to or direction",
                "expected_result": "Page is scrolled",
                "locator_strategy": "text"
            }
        ]
    
    def _create_hover_steps(self, instruction: str, start_num: int) -> List[Dict[str, Any]]:
        """Create steps for hover scenario"""
        return [
            {
                "step_number": start_num,
                "action": "hover",
                "target": "Element to hover over",
                "expected_result": "Hover action triggered",
                "locator_strategy": "text"
            }
        ]
    
    def _create_fallback_plan(self, instruction: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a basic fallback plan if all planning methods fail
        
        Args:
            instruction: The original instruction
            context: Context dictionary
            
        Returns:
            Basic plan structure
        """
        return {
            "scenario_name": "Automation Task",
            "description": instruction,
            "url": context.get('url'),
            "steps": [
                {
                    "step_number": 1,
                    "action": "execute",
                    "target": "Web application",
                    "expected_result": "Task completes successfully",
                    "locator_strategy": "auto"
                }
            ]
        }
