"""
Playwright MCP Client - Manages connection to Playwright MCP server
"""
import asyncio
import json
import logging
from typing import Any, Dict, List, Optional
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

logger = logging.getLogger(__name__)


class PlaywrightMCPClient:
    """Client for Playwright MCP server"""
    
    def __init__(self, command: str, args: List[str]):
        self.command = command
        self.args = args
        self.session: Optional[ClientSession] = None
        self.read = None
        self.write = None
        self.tools: List[Dict[str, Any]] = []
        self._stdio_context = None
        
    async def __aenter__(self):
        await self.connect()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.disconnect()
        
    async def connect(self):
        """Connect to the MCP server"""
        logger.info("Starting Playwright MCP server...")
        
        try:
            server_params = StdioServerParameters(
                command=self.command,
                args=self.args,
                env=None
            )
            
            self._stdio_context = stdio_client(server_params)
            self.read, self.write = await self._stdio_context.__aenter__()
            self.session = ClientSession(self.read, self.write)
            
            await self.session.__aenter__()
            await self.session.initialize()
            
            tools_list = await self.session.list_tools()
            self.tools = [tool.model_dump() for tool in tools_list.tools]
            
            logger.info(f"✓ MCP server connected. Available tools: {len(self.tools)}")
            
        except Exception as e:
            logger.error(f"Failed to connect to MCP server: {e}")
            raise
        
        return self
    
    async def disconnect(self):
        """Disconnect from the MCP server"""
        try:
            if self.session:
                await self.session.__aexit__(None, None, None)
            if self._stdio_context:
                await self._stdio_context.__aexit__(None, None, None)
            logger.info("MCP server disconnected")
        except Exception as e:
            logger.error(f"Error disconnecting from MCP server: {e}")
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Call a tool on the MCP server"""
        if not self.session:
            raise RuntimeError("MCP client not connected")
        
        logger.debug(f"→ Calling tool: {tool_name}")
        logger.debug(f"  Arguments: {json.dumps(arguments, indent=2)}")
        
        try:
            result = await self.session.call_tool(tool_name, arguments)
            logger.debug(f"✓ Tool executed: {tool_name}")
            return result
        except Exception as e:
            logger.error(f"Error calling tool {tool_name}: {e}")
            raise
    
    def get_tools_description(self) -> str:
        """Get a formatted description of available tools"""
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
