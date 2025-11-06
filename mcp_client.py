import asyncio
import json
import subprocess
from typing import Any, Dict, List, Optional
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from rich.console import Console

console = Console()


class PlaywrightMCPClient:
    def __init__(self, command: str, args: List[str]):
        self.command = command
        self.args = args
        self.session: Optional[ClientSession] = None
        self.read = None
        self.write = None
        self.tools: List[Dict[str, Any]] = []
        
    async def __aenter__(self):
        await self.connect()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.disconnect()
        
    async def connect(self):
        console.print("[cyan]Starting Playwright MCP server...[/cyan]")
        
        server_params = StdioServerParameters(
            command=self.command,
            args=self.args,
            env=None
        )
        
        stdio_context = stdio_client(server_params)
        self.read, self.write = await stdio_context.__aenter__()
        self.session = ClientSession(self.read, self.write)
        
        await self.session.__aenter__()
        await self.session.initialize()
        
        tools_list = await self.session.list_tools()
        self.tools = [tool.model_dump() for tool in tools_list.tools]
        
        console.print(f"[green]✓ MCP server connected. Available tools: {len(self.tools)}[/green]")
        
        return self
    
    async def disconnect(self):
        if self.session:
            await self.session.__aexit__(None, None, None)
            console.print("[cyan]MCP server disconnected[/cyan]")
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        if not self.session:
            raise RuntimeError("MCP client not connected")
        
        console.print(f"[yellow]→ Calling tool: {tool_name}[/yellow]")
        console.print(f"[dim]  Arguments: {json.dumps(arguments, indent=2)}[/dim]")
        
        result = await self.session.call_tool(tool_name, arguments)
        
        console.print(f"[green]✓ Tool executed: {tool_name}[/green]")
        
        return result
    
    def get_tools_description(self) -> str:
        if not self.tools:
            return "No tools available"
        
        descriptions = []
        for tool in self.tools:
            tool_desc = f"- {tool['name']}: {tool.get('description', 'No description')}"
            if 'inputSchema' in tool:
                props = tool['inputSchema'].get('properties', {})
                if props:
                    params = ", ".join(props.keys())
                    tool_desc += f"\n  Parameters: {params}"
            descriptions.append(tool_desc)
        
        return "\n".join(descriptions)
