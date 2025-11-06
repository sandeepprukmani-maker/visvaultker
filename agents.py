import json
import os
from typing import Any, Dict, List, Optional, Union
from anthropic import Anthropic
from openai import OpenAI
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    genai = None

from rich.console import Console
from config import (
    MODEL_CONFIGS, ModelType, EXECUTOR_SYSTEM_PROMPT,
    CODE_GENERATOR_SYSTEM_PROMPT, HEALER_SYSTEM_PROMPT, USE_OAUTH_GATEWAY
)
from mcp_client import PlaywrightMCPClient

console = Console()

# Import OAuth gateway client if enabled
if USE_OAUTH_GATEWAY:
    try:
        from llm_client import GatewayLLMClient
        GATEWAY_CLIENT = GatewayLLMClient()
    except Exception as e:
        console.print(f"[yellow]Warning: Could not initialize OAuth gateway client: {e}[/yellow]")
        console.print("[yellow]Falling back to direct API keys[/yellow]")
        GATEWAY_CLIENT = None
else:
    GATEWAY_CLIENT = None


class ExecutorAgent:
    def __init__(self, model: ModelType, mcp_client: PlaywrightMCPClient):
        self.model = model
        self.mcp_client = mcp_client
        self.execution_trace: List[Dict[str, Any]] = []
        self.model_config = MODEL_CONFIGS[model]
        self.client: Union[Anthropic, OpenAI, Any] = None
        self.use_gateway = self.model_config.get("use_gateway", False) and GATEWAY_CLIENT is not None
        
        if self.use_gateway:
            console.print(f"[cyan]Using OAuth Gen AI Gateway for {self.model_config['display_name']}[/cyan]")
            self.client = GATEWAY_CLIENT
        elif model == "claude":
            self.client = Anthropic(api_key=self.model_config["api_key"])
        elif model == "gpt4o":
            self.client = OpenAI(api_key=self.model_config["api_key"])
        elif model == "gemini":
            if GEMINI_AVAILABLE and genai:
                genai.configure(api_key=self.model_config["api_key"])
                self.client = genai.GenerativeModel(self.model_config["name"])
    
    async def execute_task(self, task_description: str) -> Dict[str, Any]:
        console.print(f"\n[bold magenta]🤖 Intelligent Executor Agent starting...[/bold magenta]")
        console.print(f"[magenta]Model: {self.model_config['display_name']}[/magenta]")
        console.print(f"[magenta]Goal: {task_description}[/magenta]\n")
        
        self.execution_trace = []
        
        tools_description = self.mcp_client.get_tools_description()
        
        prompt = f"""🎯 YOUR GOAL: {task_description}

Available Playwright MCP tools:
{tools_description}

APPROACH:
1. First, THINK about the goal and plan 2-3 possible approaches to achieve it
2. Execute your chosen approach step by step using the available tools
3. After EACH action, observe the results and adapt if needed
4. If something fails, immediately try an alternative approach
5. Be creative and autonomous - make decisions to achieve the goal
6. Use screenshots and JavaScript evaluation when you need to understand page state

Remember: You're goal-driven and intelligent. Focus on achieving the END GOAL, not just following rigid steps. Be adaptive, creative, and persistent!

Begin by reasoning about the best approach, then start execution."""
        
        # If using gateway, all models use OpenAI-compatible API
        if self.use_gateway:
            result = await self._execute_with_gateway(prompt)
        elif self.model == "claude":
            result = await self._execute_with_claude(prompt)
        elif self.model == "gpt4o":
            result = await self._execute_with_gpt4o(prompt)
        elif self.model == "gemini":
            result = await self._execute_with_gemini(prompt)
        else:
            result = {
                "success": False,
                "trace": [],
                "model": self.model,
                "error": "Unknown model"
            }
        
        return result
    
    async def _execute_with_gateway(self, prompt: str) -> Dict[str, Any]:
        """Execute using OAuth Gen AI Gateway (OpenAI-compatible API)."""
        from llm_client import GatewayLLMClient
        
        if not isinstance(self.client, GatewayLLMClient):
            raise RuntimeError("Gateway client not properly initialized")
            
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
            {"role": "system", "content": EXECUTOR_SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ]
        
        max_iterations = 30
        
        for iteration in range(max_iterations):
            response = self.client.create_chat_completion(
                model=self.model_config["name"],
                messages=messages,
                tools=tools,
                max_tokens=6000,
                temperature=0.2
            )
            
            message = response.choices[0].message
            messages.append({
                "role": "assistant",
                "content": message.content or "",
                "tool_calls": message.tool_calls
            })
            
            if not message.tool_calls:
                console.print("[green]✓ Task execution completed[/green]")
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
            "model": self.model
        }
    
    async def _execute_with_claude(self, prompt: str) -> Dict[str, Any]:
        if not isinstance(self.client, Anthropic):
            raise RuntimeError("Claude client not properly initialized")
            
        mcp_tools = []
        for tool in self.mcp_client.tools:
            mcp_tools.append({
                "name": tool["name"],
                "description": tool.get("description", ""),
                "input_schema": tool.get("inputSchema", {})
            })
        
        messages: List[Dict[str, Any]] = [{"role": "user", "content": [{"type": "text", "text": prompt}]}]
        max_iterations = 30  # Increased for more complex, goal-driven workflows
        
        for iteration in range(max_iterations):
            response = self.client.messages.create(
                model=self.model_config["name"],
                max_tokens=4096,
                system=EXECUTOR_SYSTEM_PROMPT,
                messages=messages,
                tools=mcp_tools
            )
            
            messages.append({
                "role": "assistant",
                "content": response.content
            })
            
            if response.stop_reason == "end_turn":
                console.print("[green]✓ Task execution completed[/green]")
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
            "model": self.model
        }
    
    async def _execute_with_gpt4o(self, prompt: str) -> Dict[str, Any]:
        if not isinstance(self.client, OpenAI):
            raise RuntimeError("OpenAI client not properly initialized")
            
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
            {"role": "system", "content": EXECUTOR_SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ]
        
        max_iterations = 30  # Increased for more complex, goal-driven workflows
        
        for iteration in range(max_iterations):
            response = self.client.chat.completions.create(
                model=self.model_config["name"],
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
                console.print("[green]✓ Task execution completed[/green]")
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
            "model": self.model
        }
    
    async def _execute_with_gemini(self, prompt: str) -> Dict[str, Any]:
        console.print("[yellow]Note: Gemini does not support MCP tool calling natively. Using Claude for execution.[/yellow]")
        console.print("[yellow]Switching to Claude...[/yellow]")
        
        claude_agent = ExecutorAgent("claude", self.mcp_client)
        return await claude_agent.execute_task(prompt.split("Task: ")[1].split("\n")[0])


class CodeGeneratorAgent:
    def __init__(self, model: ModelType):
        self.model = model
        self.model_config = MODEL_CONFIGS[model]
        self.client: Union[Anthropic, OpenAI, Any] = None
        self.use_gateway = self.model_config.get("use_gateway", False) and GATEWAY_CLIENT is not None
        
        if self.use_gateway:
            self.client = GATEWAY_CLIENT
        elif model == "claude":
            self.client = Anthropic(api_key=self.model_config["api_key"])
        elif model == "gpt4o":
            self.client = OpenAI(api_key=self.model_config["api_key"])
        elif model == "gemini":
            if GEMINI_AVAILABLE and genai:
                genai.configure(api_key=self.model_config["api_key"])
                self.client = genai.GenerativeModel(self.model_config["name"])
    
    async def generate_code(self, execution_trace: List[Dict[str, Any]], task_description: str) -> str:
        console.print(f"\n[bold blue]📝 Code Generator Agent starting...[/bold blue]")
        console.print(f"[blue]Model: {self.model_config['display_name']}[/blue]\n")
        
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
        
        code = ""
        if self.use_gateway:
            code = await self._generate_with_gateway(prompt)
        elif self.model == "claude":
            code = await self._generate_with_claude(prompt)
        elif self.model == "gpt4o":
            code = await self._generate_with_gpt4o(prompt)
        elif self.model == "gemini":
            code = await self._generate_with_gemini(prompt)
        
        code = self._clean_code(code)
        
        console.print("[green]✓ Code generation completed[/green]")
        return code
    
    async def _generate_with_gateway(self, prompt: str) -> str:
        """Generate code using OAuth Gen AI Gateway."""
        from llm_client import GatewayLLMClient
        
        if not isinstance(self.client, GatewayLLMClient):
            raise RuntimeError("Gateway client not properly initialized")
        
        response = self.client.create_chat_completion(
            model=self.model_config["name"],
            messages=[
                {"role": "system", "content": CODE_GENERATOR_SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            max_tokens=6000,
            temperature=0.2
        )
        
        return response.choices[0].message.content or ""
    
    async def _generate_with_claude(self, prompt: str) -> str:
        if not isinstance(self.client, Anthropic):
            raise RuntimeError("Claude client not properly initialized")
            
        response = self.client.messages.create(
            model=self.model_config["name"],
            max_tokens=4096,
            system=CODE_GENERATOR_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": [{"type": "text", "text": prompt}]}]
        )
        
        for block in response.content:
            if hasattr(block, 'text'):
                return block.text
        
        return ""
    
    async def _generate_with_gpt4o(self, prompt: str) -> str:
        if not isinstance(self.client, OpenAI):
            raise RuntimeError("OpenAI client not properly initialized")
            
        response = self.client.chat.completions.create(
            model=self.model_config["name"],
            messages=[
                {"role": "system", "content": CODE_GENERATOR_SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ]
        )
        
        return response.choices[0].message.content or ""
    
    async def _generate_with_gemini(self, prompt: str) -> str:
        if not GEMINI_AVAILABLE or not genai or not self.client:
            raise RuntimeError("Gemini client not properly initialized")
            
        full_prompt = f"{CODE_GENERATOR_SYSTEM_PROMPT}\n\n{prompt}"
        response = self.client.generate_content(full_prompt)
        return response.text if hasattr(response, 'text') else ""
    
    def _clean_code(self, code: str) -> str:
        code = code.strip()
        
        if code.startswith("```python"):
            code = code[9:]
        elif code.startswith("```"):
            code = code[3:]
        
        if code.endswith("```"):
            code = code[:-3]
        
        return code.strip()


class HealerAgent:
    def __init__(self, model: ModelType):
        self.model = model
        self.model_config = MODEL_CONFIGS[model]
        self.client: Union[Anthropic, OpenAI, Any] = None
        self.use_gateway = self.model_config.get("use_gateway", False) and GATEWAY_CLIENT is not None
        
        if self.use_gateway:
            self.client = GATEWAY_CLIENT
        elif model == "claude":
            self.client = Anthropic(api_key=self.model_config["api_key"])
        elif model == "gpt4o":
            self.client = OpenAI(api_key=self.model_config["api_key"])
        elif model == "gemini":
            if GEMINI_AVAILABLE and genai:
                genai.configure(api_key=self.model_config["api_key"])
                self.client = genai.GenerativeModel(self.model_config["name"])
    
    async def heal_code(self, original_code: str, error_message: str, trace_file: Optional[str] = None) -> str:
        console.print(f"\n[bold red]🔧 Healer Agent starting...[/bold red]")
        console.print(f"[red]Model: {self.model_config['display_name']}[/red]\n")
        
        trace_info = ""
        if trace_file and os.path.exists(trace_file):
            trace_info = f"\n\nPlaywright trace file available at: {trace_file}"
        
        prompt = f"""The following Playwright script failed with an error:

ORIGINAL CODE:
{original_code}

ERROR:
{error_message}
{trace_info}

Analyze the error and fix the script. Common issues:
1. Incorrect selectors - use more robust locators
2. Timing issues - add proper waits
3. Element not found - verify element exists before interacting
4. Use intelligent locators (get_by_role, get_by_label, etc.) instead of CSS

Output ONLY the fixed Python code, no explanations."""
        
        code = ""
        if self.use_gateway:
            code = await self._heal_with_gateway(prompt)
        elif self.model == "claude":
            code = await self._heal_with_claude(prompt)
        elif self.model == "gpt4o":
            code = await self._heal_with_gpt4o(prompt)
        elif self.model == "gemini":
            code = await self._heal_with_gemini(prompt)
        
        code = self._clean_code(code)
        
        console.print("[green]✓ Code healing completed[/green]")
        return code
    
    async def _heal_with_gateway(self, prompt: str) -> str:
        """Heal code using OAuth Gen AI Gateway."""
        from llm_client import GatewayLLMClient
        
        if not isinstance(self.client, GatewayLLMClient):
            raise RuntimeError("Gateway client not properly initialized")
        
        response = self.client.create_chat_completion(
            model=self.model_config["name"],
            messages=[
                {"role": "system", "content": HEALER_SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            max_tokens=6000,
            temperature=0.2
        )
        
        return response.choices[0].message.content or ""
    
    async def _heal_with_claude(self, prompt: str) -> str:
        if not isinstance(self.client, Anthropic):
            raise RuntimeError("Claude client not properly initialized")
            
        response = self.client.messages.create(
            model=self.model_config["name"],
            max_tokens=4096,
            system=HEALER_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": [{"type": "text", "text": prompt}]}]
        )
        
        for block in response.content:
            if hasattr(block, 'text'):
                return block.text
        
        return ""
    
    async def _heal_with_gpt4o(self, prompt: str) -> str:
        if not isinstance(self.client, OpenAI):
            raise RuntimeError("OpenAI client not properly initialized")
            
        response = self.client.chat.completions.create(
            model=self.model_config["name"],
            messages=[
                {"role": "system", "content": HEALER_SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ]
        )
        
        return response.choices[0].message.content or ""
    
    async def _heal_with_gemini(self, prompt: str) -> str:
        if not GEMINI_AVAILABLE or not genai or not self.client:
            raise RuntimeError("Gemini client not properly initialized")
            
        full_prompt = f"{HEALER_SYSTEM_PROMPT}\n\n{prompt}"
        response = self.client.generate_content(full_prompt)
        return response.text if hasattr(response, 'text') else ""
    
    def _clean_code(self, code: str) -> str:
        code = code.strip()
        
        if code.startswith("```python"):
            code = code[9:]
        elif code.startswith("```"):
            code = code[3:]
        
        if code.endswith("```"):
            code = code[:-3]
        
        return code.strip()
