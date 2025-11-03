"""
Playwright MCP Codebase
Tool-based browser automation using Playwright's Model Context Protocol
"""
from app.engines.playwright_mcp.client.stdio_client import MCPStdioClient
from app.engines.playwright_mcp.agent.conversation_agent import BrowserAgent
from app.engines.playwright_mcp.server_manager import get_mcp_client, get_server_status, shutdown_server


def create_engine(headless: bool = False):
    """
    Factory function to create a Playwright MCP engine instance
    
    Uses server manager to handle both 'always_run' and 'on_demand' modes.
    The server mode is configured in config/config.ini under [playwright_mcp].
    
    Args:
        headless: Run browser in headless mode
        
    Returns:
        Tuple of (mcp_client, browser_agent)
    """
    mcp_client = get_mcp_client(headless=headless)
    browser_agent = BrowserAgent(mcp_client)
    return mcp_client, browser_agent


__all__ = ['MCPStdioClient', 'BrowserAgent', 'create_engine', 'get_server_status', 'shutdown_server']
