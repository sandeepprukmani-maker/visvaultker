"""
Playwright MCP Codebase
Tool-based browser automation using Playwright's Model Context Protocol

Now includes optimized client with performance enhancements:
- Batch execution (70-80% token reduction)
- Smart snapshot inclusion
- Performance metrics tracking
"""
from app.engines.playwright_mcp.client.stdio_client import MCPStdioClient
from app.engines.playwright_mcp.client.optimized_client import OptimizedMCPClient, SnapshotMode
from app.engines.playwright_mcp.agent.conversation_agent import BrowserAgent
from app.engines.playwright_mcp.server_manager import get_mcp_client, get_server_status, shutdown_server
from app.engines.playwright_mcp.optimized_manager import (
    get_optimized_mcp_client, 
    get_server_status as get_optimized_server_status,
    reset_server_metrics,
    shutdown_optimized_server
)


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


def create_optimized_engine(headless: bool = False):
    """
    Factory function to create an OPTIMIZED Playwright MCP engine instance
    
    Performance features:
    - Batch execution for 3+ operations (70-80% token reduction)
    - Smart snapshot inclusion (saves tokens)
    - Performance metrics tracking
    - Connection pooling
    
    Args:
        headless: Run browser in headless mode
        
    Returns:
        OptimizedMCPClient instance with enhanced performance
    """
    return get_optimized_mcp_client(headless=headless)


__all__ = [
    'MCPStdioClient', 
    'OptimizedMCPClient',
    'SnapshotMode',
    'BrowserAgent', 
    'create_engine',
    'create_optimized_engine',
    'get_server_status', 
    'get_optimized_server_status',
    'reset_server_metrics',
    'shutdown_server',
    'shutdown_optimized_server'
]
