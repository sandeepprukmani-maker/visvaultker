"""
AI Agents for Playwright MCP Engine
"""
import json
import logging
from typing import Any, Dict, List, Union
from anthropic import Anthropic
from openai import OpenAI

logger = logging.getLogger(__name__)


class MCPExecutorAgent:
    """Agent that executes browser automation tasks using MCP tools"""
    
    def __init__(self, model_name: str, api_key: str, mcp_client):
        self.model_name = model_name
        self.api_key = api_key
        self.mcp_client = mcp_client
        self.execution_trace: List[Dict[str, Any]] = []
        
        # Determine which LLM client to use
        if "claude" in model_name.lower() or "anthropic" in model_name.lower():
            self.client = Anthropic(api_key=api_key)
            self.client_type = "claude"
        elif "gpt" in model_name.lower() or "openai" in model_name.lower():
            self.client = OpenAI(api_key=api_key)
            self.client_type = "openai"
        else:
            # Default to claude
            self.client = Anthropic(api_key=api_key)
            self.client_type = "claude"
    
    async def execute_task(self, task_description: str) -> Dict[str, Any]:
        """Execute a browser automation task"""
        logger.info(f"🤖 MCPExecutorAgent starting task: {task_description}")
        
        self.execution_trace = []
        
        tools_description = self.mcp_client.get_tools_description()
        
        system_prompt = """You are a browser automation expert. Your task is to perform web automation using Playwright MCP tools.

When performing tasks:
1. Use accessible selectors (role, label, placeholder, test-id) when possible
2. Navigate step by step
3. Verify actions were successful
4. Be precise with selectors

Describe each action clearly as you perform it."""
        
        prompt = f"""Task: {task_description}

Available Playwright MCP tools:
{tools_description}

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
