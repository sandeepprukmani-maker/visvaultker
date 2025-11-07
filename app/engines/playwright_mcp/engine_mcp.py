"""
Playwright MCP Engine - Main engine for MCP-based automation
"""
import asyncio
import logging
import os
import json
import configparser
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

from .mcp_client import PlaywrightMCPClient
from .ai_agents import MCPExecutorAgent, CodeGeneratorAgent
from auth.oauth_handler import get_oauth_token_with_retry

logger = logging.getLogger(__name__)


class PlaywrightMCPEngine:
    """Main engine for Playwright MCP-based browser automation with persistent MCP client"""
    
    # Class-level persistent MCP client (shared across all instances)
    _persistent_client: Optional[PlaywrightMCPClient] = None
    _client_lock: Optional[asyncio.Lock] = None
    
    def __init__(self):
        self.config = self._load_config()
        self.mcp_command = "npx"
        self.mcp_args = ["@playwright/mcp"]
        self._mcp_client: Optional[PlaywrightMCPClient] = None
        
        # Setup screenshot directory
        self.screenshots_dir = Path("automation_outputs") / "screenshots"
        self.screenshots_dir.mkdir(parents=True, exist_ok=True)
        logger.debug(f"📁 Screenshots directory: {self.screenshots_dir}")
    
    @classmethod
    def _get_lock(cls) -> asyncio.Lock:
        """Lazily create the lock in async context (avoids import-time event loop error)"""
        if cls._client_lock is None:
            cls._client_lock = asyncio.Lock()
        return cls._client_lock
        
    def _load_config(self) -> configparser.ConfigParser:
        """Load configuration from config.ini"""
        config = configparser.ConfigParser()
        config_path = Path(__file__).parent.parent.parent.parent / 'config' / 'config.ini'
        
        if config_path.exists():
            config.read(config_path)
        
        return config
    
    async def _get_or_create_persistent_client(self) -> PlaywrightMCPClient:
        """
        Get or create the persistent MCP client (pre-warmed, reusable)
        This eliminates the 5s cold start on every task
        """
        async with self._get_lock():
            # Check if client exists and is healthy
            if self._persistent_client is not None:
                try:
                    # Quick health check - verify tools are still available
                    if self._persistent_client.tools and len(self._persistent_client.tools) > 0:
                        logger.info("♻️  Reusing existing MCP client (pre-warmed)")
                        return self._persistent_client
                    else:
                        logger.warning("⚠️  Persistent client unhealthy, reconnecting...")
                except:
                    logger.warning("⚠️  Persistent client error, reconnecting...")
            
            # Create new persistent client
            logger.info("🔄 Creating persistent MCP client (one-time 5s startup)...")
            client = PlaywrightMCPClient(self.mcp_command, self.mcp_args)
            await client.connect()
            
            # Store as class-level persistent client
            PlaywrightMCPEngine._persistent_client = client
            logger.info(f"✅ Persistent MCP client ready with {len(client.tools)} tools")
            
            return client
    
    @classmethod
    async def cleanup_persistent_client(cls):
        """Cleanup the persistent client (call on shutdown)"""
        if cls._persistent_client:
            try:
                await cls._persistent_client.disconnect()
                logger.info("🔌 Persistent MCP client disconnected")
            except:
                pass
            finally:
                cls._persistent_client = None
    
    async def run_task(self, task_description: str, headless: bool = True, **kwargs) -> Dict[str, Any]:
        """
        Run an automation task using Playwright MCP
        Supports both OAuth (like Browser Use) and direct API keys
        
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
        api_key = None
        use_oauth = False
        
        gateway_base_url = os.environ.get('GW_BASE_URL', '')
        if gateway_base_url:
            try:
                logger.info("🔐 Using OAuth authentication (like Browser Use)")
                api_key = get_oauth_token_with_retry(max_retries=3)
                use_oauth = True
                logger.info("✅ OAuth token obtained successfully")
            except Exception as e:
                logger.warning(f"⚠️  OAuth authentication failed: {e}")
                logger.info("📋 Falling back to direct API keys...")
        
        if not api_key:
            api_key = kwargs.get('api_key', os.environ.get('OPENAI_API_KEY', ''))
        
        if not api_key:
            api_key = os.environ.get('ANTHROPIC_API_KEY', '')
            if api_key:
                model_name = 'claude-sonnet-4-20250514'
                logger.info("🤖 Using Anthropic Claude model")
        
        if not api_key:
            error_msg = "No API key found. Please set up OAuth (GW_BASE_URL + OAuth env vars) or set OPENAI_API_KEY/ANTHROPIC_API_KEY."
            logger.error(f"❌ {error_msg}")
            return {
                "success": False,
                "error": error_msg,
                "result": None
            }
        
        try:
            # Get or create persistent MCP client (eliminates 5s cold start!)
            mcp_client = await self._get_or_create_persistent_client()
            self._mcp_client = mcp_client
            
            # Create executor agent
            # Pass gateway_base_url if using OAuth, otherwise pass None for direct API access
            base_url = gateway_base_url if use_oauth else None
            executor = MCPExecutorAgent(model_name, api_key, mcp_client, base_url=base_url)
            
            # Execute the task with headless preference
            result = await executor.execute_task(task_description, headless=headless)
            
            if result["success"]:
                logger.info("✓ Task completed successfully")
                
                # Capture final screenshot
                screenshot_paths = []
                try:
                    logger.info("📸 Capturing final screenshot...")
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"final_{timestamp}.png"
                    filepath = self.screenshots_dir / filename
                    
                    # Use MCP client to capture screenshot
                    screenshot_result = await mcp_client.call_tool(
                        "playwright_screenshot",
                        {"path": str(filepath), "fullPage": True}
                    )
                    
                    if screenshot_result and not screenshot_result.get("isError"):
                        screenshot_paths.append(str(filepath))
                        logger.info(f"📸 Final screenshot captured: {filepath}")
                    else:
                        logger.warning(f"⚠️  Screenshot capture returned error: {screenshot_result}")
                        
                except Exception as e:
                    logger.warning(f"⚠️  Failed to capture final screenshot: {e}")
                
                # Generate Python code from execution trace
                try:
                    logger.info("📝 Generating Python code from execution trace...")
                    code_generator = CodeGeneratorAgent(model_name, api_key, base_url=base_url)
                    playwright_code = await code_generator.generate_code(
                        result["trace"], 
                        task_description
                    )
                    logger.info("✓ Python code generation completed")
                except Exception as e:
                    logger.warning(f"⚠️  Code generation failed: {e}")
                    playwright_code = None
                
                return {
                    "success": True,
                    "result": {
                        "message": "Task completed successfully",
                        "trace": result["trace"],
                        "model": result["model"]
                    },
                    "screenshot_paths": screenshot_paths,
                    "playwright_code": playwright_code,
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
            # On error, cleanup the persistent client
            try:
                await self.cleanup_persistent_client()
            except:
                pass
            return {
                "success": False,
                "error": str(e),
                "result": None
            }
        finally:
            # Don't set to None - we want to keep the persistent client alive
            pass
    
    async def health_check(self) -> Dict[str, Any]:
        """Check if the MCP engine is healthy and ready (uses persistent client)"""
        try:
            # Try to get or create persistent client
            mcp_client = await self._get_or_create_persistent_client()
            tools_count = len(mcp_client.tools)
            return {
                "healthy": True,
                "message": f"MCP server connected with {tools_count} tools available (persistent mode)",
                "tools_count": tools_count,
                "persistent": True
            }
        except Exception as e:
            return {
                "healthy": False,
                "message": f"MCP server connection failed: {str(e)}",
                "error": str(e),
                "persistent": False
            }
