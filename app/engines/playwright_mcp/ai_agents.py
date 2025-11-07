"""
AI Agents for Playwright MCP Engine
"""
import json
import logging
from typing import Any, Dict, List, Union
from anthropic import Anthropic
from openai import OpenAI

logger = logging.getLogger(__name__)

CODE_GENERATOR_SYSTEM_PROMPT = """You are a Python code generation expert. Convert browser automation execution traces into clean, reusable Playwright Python scripts.

Requirements:
1. Use async/await patterns properly
2. Prioritize intelligent locators in this order:
   - page.get_by_role()
   - page.get_by_label()
   - page.get_by_placeholder()
   - page.get_by_test_id()
   - page.locator() (CSS) only as last resort
3. Include proper imports
4. Use descriptive variable names
5. Add comments for clarity
6. Create a single, executable Python function
7. Handle errors gracefully
8. Structure code cleanly with proper spacing

Generate ONLY the Python code, no explanations."""


class MCPExecutorAgent:
    """Agent that executes browser automation tasks using MCP tools"""
    
    def __init__(self, model_name: str, api_key: str, mcp_client, base_url: str = None):
        self.model_name = model_name
        self.api_key = api_key
        self.mcp_client = mcp_client
        self.base_url = base_url
        self.execution_trace: List[Dict[str, Any]] = []
        
        # Determine which LLM client to use
        if "claude" in model_name.lower() or "anthropic" in model_name.lower():
            self.client = Anthropic(api_key=api_key)
            self.client_type = "claude"
        elif "gpt" in model_name.lower() or "openai" in model_name.lower():
            if base_url:
                logger.info(f"🔐 Using OAuth gateway: {base_url}")
                self.client = OpenAI(api_key=api_key, base_url=base_url)
            else:
                self.client = OpenAI(api_key=api_key)
            self.client_type = "openai"
        else:
            # Default to OpenAI with gateway if base_url provided
            if base_url:
                logger.info(f"🔐 Using OAuth gateway: {base_url}")
                self.client = OpenAI(api_key=api_key, base_url=base_url)
                self.client_type = "openai"
            else:
                self.client = Anthropic(api_key=api_key)
                self.client_type = "claude"
    
    async def execute_task(self, task_description: str, headless: bool = True) -> Dict[str, Any]:
        """Execute a browser automation task"""
        logger.info(f"🤖 MCPExecutorAgent starting task: {task_description} (headless={headless})")
        
        self.execution_trace = []
        
        tools_description = self.mcp_client.get_tools_description()
        
        browser_mode = "headless mode (no visible window)" if headless else "headful mode (visible browser window)"
        
        system_prompt = f"""You are a browser automation expert. Your task is to perform web automation using Playwright MCP tools.

IMPORTANT: When launching the browser, you MUST run it in {browser_mode}.
For any playwright_launch or browser launch tool calls, set headless parameter to {str(headless).lower()}.

When performing tasks:
1. Launch browser in {browser_mode}
2. Use accessible selectors (role, label, placeholder, test-id) when possible
3. Navigate step by step
4. Verify actions were successful
5. Be precise with selectors

Describe each action clearly as you perform it."""
        
        prompt = f"""Task: {task_description}

Available Playwright MCP tools:
{tools_description}

REMEMBER: Launch the browser in {browser_mode} (headless={str(headless).lower()}).

Execute this task step by step using the available tools. After each action, describe what you did and what you observe."""
        
        if self.client_type == "claude":
            result = await self._execute_with_claude(prompt, system_prompt)
        else:
            result = await self._execute_with_openai(prompt, system_prompt)
        
        return result
    
    async def _execute_with_claude(self, prompt: str, system_prompt: str) -> Dict[str, Any]:
        """Execute task using Claude"""
        mcp_tools = []
        for tool in self.mcp_client.tools:
            mcp_tools.append({
                "name": tool["name"],
                "description": tool.get("description", ""),
                "input_schema": tool.get("inputSchema", {})
            })
        
        messages: List[Dict[str, Any]] = [
            {"role": "user", "content": [{"type": "text", "text": prompt}]}
        ]
        max_iterations = 20
        
        try:
            for iteration in range(max_iterations):
                response = self.client.messages.create(
                    model=self.model_name,
                    max_tokens=4096,
                    system=system_prompt,
                    messages=messages,
                    tools=mcp_tools
                )
                
                messages.append({
                    "role": "assistant",
                    "content": response.content
                })
                
                if response.stop_reason == "end_turn":
                    logger.info("✓ Task execution completed")
                    break
                
                if response.stop_reason == "tool_use":
                    tool_results = []
                    
                    for block in response.content:
                        if block.type == "tool_use":
                            tool_name = block.name
                            tool_input = block.input
                            
                            self.execution_trace.append({
                                "type": "tool_call",
                                "tool": tool_name,
                                "arguments": tool_input
                            })
                            
                            result = await self.mcp_client.call_tool(tool_name, tool_input)
                            
                            result_content = []
                            for content_item in result.content:
                                if hasattr(content_item, 'text'):
                                    result_content.append(content_item.text)
                            
                            result_text = "\n".join(result_content)
                            
                            self.execution_trace.append({
                                "type": "tool_result",
                                "tool": tool_name,
                                "result": result_text
                            })
                            
                            tool_results.append({
                                "type": "tool_result",
                                "tool_use_id": block.id,
                                "content": [{"type": "text", "text": result_text}]
                            })
                    
                    messages.append({
                        "role": "user",
                        "content": tool_results
                    })
            
            return {
                "success": True,
                "trace": self.execution_trace,
                "model": self.model_name
            }
        except Exception as e:
            logger.error(f"Error during task execution: {e}")
            return {
                "success": False,
                "trace": self.execution_trace,
                "model": self.model_name,
                "error": str(e)
            }
    
    async def _execute_with_openai(self, prompt: str, system_prompt: str) -> Dict[str, Any]:
        """Execute task using OpenAI"""
        tools = []
        for tool in self.mcp_client.tools:
            tools.append({
                "type": "function",
                "function": {
                    "name": tool["name"],
                    "description": tool.get("description", ""),
                    "parameters": tool.get("inputSchema", {})
                }
            })
        
        messages: List[Dict[str, Any]] = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ]
        
        max_iterations = 20
        
        try:
            for iteration in range(max_iterations):
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=messages,
                    tools=tools
                )
                
                message = response.choices[0].message
                messages.append({
                    "role": "assistant",
                    "content": message.content or "",
                    "tool_calls": message.tool_calls
                })
                
                if not message.tool_calls:
                    logger.info("✓ Task execution completed")
                    break
                
                for tool_call in message.tool_calls:
                    tool_name = tool_call.function.name
                    tool_args = json.loads(tool_call.function.arguments)
                    
                    self.execution_trace.append({
                        "type": "tool_call",
                        "tool": tool_name,
                        "arguments": tool_args
                    })
                    
                    result = await self.mcp_client.call_tool(tool_name, tool_args)
                    
                    result_content = []
                    for content_item in result.content:
                        if hasattr(content_item, 'text'):
                            result_content.append(content_item.text)
                    
                    result_text = "\n".join(result_content)
                    
                    self.execution_trace.append({
                        "type": "tool_result",
                        "tool": tool_name,
                        "result": result_text
                    })
                    
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": result_text
                    })
            
            return {
                "success": True,
                "trace": self.execution_trace,
                "model": self.model_name
            }
        except Exception as e:
            logger.error(f"Error during task execution: {e}")
            return {
                "success": False,
                "trace": self.execution_trace,
                "model": self.model_name,
                "error": str(e)
            }


class CodeGeneratorAgent:
    """Agent that generates Python Playwright code from execution traces"""
    
    def __init__(self, model_name: str, api_key: str, base_url: str = None):
        self.model_name = model_name
        self.api_key = api_key
        self.base_url = base_url
        
        # Determine which LLM client to use
        if "claude" in model_name.lower() or "anthropic" in model_name.lower():
            self.client = Anthropic(api_key=api_key)
            self.client_type = "claude"
        elif "gpt" in model_name.lower() or "openai" in model_name.lower():
            if base_url:
                self.client = OpenAI(api_key=api_key, base_url=base_url)
            else:
                self.client = OpenAI(api_key=api_key)
            self.client_type = "openai"
        else:
            # Default to OpenAI
            if base_url:
                self.client = OpenAI(api_key=api_key, base_url=base_url)
            else:
                self.client = OpenAI(api_key=api_key)
            self.client_type = "openai"
    
    async def generate_code(self, execution_trace: List[Dict[str, Any]], task_description: str) -> str:
        """Generate Python Playwright code from execution trace"""
        logger.info(f"📝 Code Generator Agent starting for task: {task_description}")
        
        trace_text = json.dumps(execution_trace, indent=2)
        
        prompt = f"""Task Description: {task_description}

Execution Trace:
{trace_text}

Generate a clean, production-ready Python Playwright script that performs this automation task.

Use intelligent locators:
1. page.get_by_role() - for buttons, links, headings, etc.
2. page.get_by_label() - for form fields with labels
3. page.get_by_placeholder() - for inputs with placeholders
4. page.get_by_test_id() - for elements with test IDs
5. page.locator() - only as last resort for CSS selectors

Include:
- Proper async/await structure
- All necessary imports
- Error handling
- Descriptive variable names
- Comments where helpful

Output ONLY the Python code, starting with imports."""
        
        try:
            if self.client_type == "claude":
                code = await self._generate_with_claude(prompt)
            else:
                code = await self._generate_with_openai(prompt)
            
            code = self._clean_code(code)
            logger.info("✓ Code generation completed")
            return code
        except Exception as e:
            logger.error(f"Error generating code: {e}")
            return f"# Error generating code: {str(e)}\n"
    
    async def _generate_with_claude(self, prompt: str) -> str:
        """Generate code using Claude"""
        response = self.client.messages.create(
            model=self.model_name,
            max_tokens=4096,
            system=CODE_GENERATOR_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": [{"type": "text", "text": prompt}]}]
        )
        
        for block in response.content:
            if hasattr(block, 'text'):
                return block.text
        
        return ""
    
    async def _generate_with_openai(self, prompt: str) -> str:
        """Generate code using OpenAI"""
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[
                {"role": "system", "content": CODE_GENERATOR_SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ]
        )
        
        return response.choices[0].message.content or ""
    
    def _clean_code(self, code: str) -> str:
        """Clean generated code by removing markdown formatting"""
        code = code.strip()
        
        if code.startswith("```python"):
            code = code[9:]
        elif code.startswith("```"):
            code = code[3:]
        
        if code.endswith("```"):
            code = code[:-3]
        
        return code.strip()
