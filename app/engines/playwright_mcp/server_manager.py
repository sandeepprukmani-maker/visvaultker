"""
Playwright MCP Server Manager
Manages persistent MCP server instance when running in 'always_run' mode
"""
import configparser
import logging
import threading
from typing import Optional
from app.engines.playwright_mcp.client.stdio_client import MCPStdioClient

logger = logging.getLogger(__name__)


class MCPServerManager:
    """
    Singleton manager for Playwright MCP server
    
    Supports two modes:
    - always_run: Keep server running continuously (faster, uses more resources)
    - on_demand: Start server only when needed (saves resources)
    """
    
    _instance = None
    _lock = threading.Lock()
    _server_instance: Optional[MCPStdioClient] = None
    _server_mode = "on_demand"
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._load_config()
        return cls._instance
    
    def _load_config(self):
        """Load configuration from config.ini"""
        config = configparser.ConfigParser()
        try:
            config.read('config/config.ini')
            if config.has_section('playwright_mcp'):
                self._server_mode = config.get('playwright_mcp', 'server_mode', fallback='on_demand')
                logger.info(f"🔧 MCP Server mode: {self._server_mode}")
            else:
                logger.warning("⚠️  No [playwright_mcp] section in config, using on_demand mode")
        except Exception as e:
            logger.error(f"❌ Failed to load MCP config: {e}, using on_demand mode")
    
    def get_client(self, headless: bool = True, browser: str = 'chromium') -> MCPStdioClient:
        """
        Get MCP client instance based on server mode
        
        Args:
            headless: Run browser in headless mode
            browser: Browser type to use
            
        Returns:
            MCPStdioClient instance
        """
        if self._server_mode == "always_run":
            return self._get_persistent_client(headless, browser)
        else:
            return self._create_new_client(headless, browser)
    
    def _get_persistent_client(self, headless: bool, browser: str) -> MCPStdioClient:
        """
        Get or create persistent MCP client for 'always_run' mode
        
        Args:
            headless: Run browser in headless mode
            browser: Browser type to use
            
        Returns:
            Persistent MCPStdioClient instance
        """
        with self._lock:
            if self._server_instance is None:
                logger.info("🚀 Starting persistent MCP server (always_run mode)")
                self._server_instance = MCPStdioClient(headless=headless, browser=browser)
                try:
                    self._server_instance.initialize()
                    logger.info("✅ Persistent MCP server started and initialized")
                except Exception as e:
                    logger.error(f"❌ Failed to initialize persistent MCP server: {e}")
                    self._server_instance = None
                    raise
            else:
                # Check if server is still alive
                if self._server_instance.process and self._server_instance.process.poll() is not None:
                    logger.warning("⚠️  Persistent MCP server died, restarting...")
                    self._server_instance = MCPStdioClient(headless=headless, browser=browser)
                    try:
                        self._server_instance.initialize()
                        logger.info("✅ Persistent MCP server restarted")
                    except Exception as e:
                        logger.error(f"❌ Failed to restart persistent MCP server: {e}")
                        self._server_instance = None
                        raise
            
            return self._server_instance
    
    def _create_new_client(self, headless: bool, browser: str) -> MCPStdioClient:
        """
        Create new MCP client for 'on_demand' mode
        
        Args:
            headless: Run browser in headless mode
            browser: Browser type to use
            
        Returns:
            New MCPStdioClient instance
        """
        logger.info("🔄 Creating on-demand MCP client")
        client = MCPStdioClient(headless=headless, browser=browser)
        try:
            client.initialize()
            logger.info("✅ On-demand MCP client initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize on-demand MCP client: {e}")
            raise
        return client
    
    def shutdown_persistent_server(self):
        """Shutdown the persistent MCP server if running"""
        with self._lock:
            if self._server_instance is not None:
                logger.info("🛑 Shutting down persistent MCP server")
                try:
                    self._server_instance.cleanup()
                    logger.info("✅ Persistent MCP server shut down")
                except Exception as e:
                    logger.error(f"⚠️  Error during server shutdown: {e}")
                finally:
                    self._server_instance = None
    
    def get_server_mode(self) -> str:
        """Get current server mode (always_run or on_demand)"""
        return self._server_mode
    
    def is_persistent_server_running(self) -> bool:
        """Check if persistent server is running"""
        if self._server_mode != "always_run":
            return False
        
        with self._lock:
            if self._server_instance is None:
                return False
            
            if self._server_instance.process is None:
                return False
            
            return self._server_instance.process.poll() is None


# Global instance
_manager = MCPServerManager()


def get_mcp_client(headless: bool = True, browser: str = 'chromium') -> MCPStdioClient:
    """
    Get MCP client instance (convenience function)
    
    Args:
        headless: Run browser in headless mode
        browser: Browser type to use
        
    Returns:
        MCPStdioClient instance
    """
    return _manager.get_client(headless=headless, browser=browser)


def shutdown_server():
    """Shutdown persistent MCP server if running (convenience function)"""
    _manager.shutdown_persistent_server()


def get_server_status() -> dict:
    """Get server status information"""
    return {
        'mode': _manager.get_server_mode(),
        'persistent_running': _manager.is_persistent_server_running()
    }
