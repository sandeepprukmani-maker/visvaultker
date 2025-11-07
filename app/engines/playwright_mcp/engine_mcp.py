"""
Playwright MCP Engine - Main engine for MCP-based automation
"""
import asyncio
import logging
import os
import configparser
from pathlib import Path
from typing import Dict, Any, Optional

from .mcp_client import PlaywrightMCPClient
from .ai_agents import MCPExecutorAgent

logger = logging.getLogger(__name__)


class PlaywrightMCPEngine:
    """Main engine for Playwright MCP-based browser automation"""
    
    def __init__(self):
        self.config = self._load_config()
        self.mcp_command = "npx"
        self.mcp_args = ["@playwright/mcp"]
        self._mcp_client: Optional[PlaywrightMCPClient] = None
        
    def _load_config(self) -> configparser.ConfigParser:
        """Load configuration from config.ini"""
        config = configparser.ConfigParser()
        config_path = Path(__file__).parent.parent.parent.parent / 'config' / 'config.ini'
        
        if config_path.exists():
            config.read(config_path)
        
        return config
    
    async def run_task(self, task_description: str, headless: bool = True, **kwargs) -> Dict[str, Any]:
        """
        Run an automation task using Playwright MCP
        
        Args:
            task_description: Natural language description of the task
            headless: Whether to run browser in headless mode
            **kwargs: Additional parameters (model_name, api_key, etc.)
        
        Returns:
            Dictionary with task execution results
        """
        logger.info(f"🚀 Playwright MCP Engine starting task: {task_description} (headless={headless})")
        
        # Get model configuration
        model_name = kwargs.get('model_name', self.config.get('openai', 'model', fallback='gpt-4o'))
        api_key = kwargs.get('api_key', os.environ.get('OPENAI_API_KEY', ''))
        
        if not api_key:
            # Try Anthropic key if OpenAI not available
            api_key = os.environ.get('ANTHROPIC_API_KEY', '')
            if api_key:
                model_name = 'claude-sonnet-4-20250514'
        
        if not api_key:
            return {
                "success": False,
                "error": "No API key found. Please set OPENAI_API_KEY or ANTHROPIC_API_KEY environment variable.",
                "result": None
            }
        
        try:
            # Connect to MCP server
            async with PlaywrightMCPClient(self.mcp_command, self.mcp_args) as mcp_client:
                self._mcp_client = mcp_client
                
                # Create executor agent
                executor = MCPExecutorAgent(model_name, api_key, mcp_client)
                
                # Execute the task with headless preference
                result = await executor.execute_task(task_description, headless=headless)
                
                if result["success"]:
                    logger.info("✓ Task completed successfully")
                    return {
                        "success": True,
                        "result": {
                            "message": "Task completed successfully",
                            "trace": result["trace"],
                            "model": result["model"]
                        },
                        "error": None
                    }
                else:
                    logger.error(f"Task execution failed: {result.get('error', 'Unknown error')}")
                    return {
                        "success": False,
                        "error": result.get('error', 'Task execution failed'),
                        "result": {"trace": result["trace"]}
                    }
                
        except Exception as e:
            logger.error(f"Error running MCP engine: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "result": None
            }
        finally:
            self._mcp_client = None
    
    async def health_check(self) -> Dict[str, Any]:
        """Check if the MCP engine is healthy and ready"""
        try:
            # Try to connect to MCP server
            async with PlaywrightMCPClient(self.mcp_command, self.mcp_args) as mcp_client:
                tools_count = len(mcp_client.tools)
                return {
                    "healthy": True,
                    "message": f"MCP server connected with {tools_count} tools available",
                    "tools_count": tools_count
                }
        except Exception as e:
            return {
                "healthy": False,
                "message": f"MCP server connection failed: {str(e)}",
                "error": str(e)
            }
