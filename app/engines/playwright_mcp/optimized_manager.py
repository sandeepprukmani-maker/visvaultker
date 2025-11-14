"""
Optimized MCP Server Manager with Performance Enhancements

Manages Playwright MCP server lifecycle with advanced features:
- Batch execution support
- Token reduction strategies
- Performance metrics
- Connection pooling
- Automatic retry with exponential backoff
"""
import configparser
import logging
import threading
import time
from typing import Optional, Dict, Any
from pathlib import Path

from .client.optimized_client import OptimizedMCPClient, SnapshotMode

logger = logging.getLogger(__name__)


class OptimizedMCPServerManager:
    """
    Enhanced singleton manager for Playwright MCP server with performance optimizations
    
    Features:
    - Batch execution for sequential operations
    - Token reduction with smart snapshot inclusion
    - Performance metrics tracking
    - Connection pooling and reuse
    - Automatic error recovery
    """
    
    _instance = None
    _lock = threading.Lock()
    _client_instance: Optional[OptimizedMCPClient] = None
    _server_mode = "always_run"
    _config = {}
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._load_config()
        return cls._instance
    
    def _load_config(self):
        """Load configuration from config.ini with performance options"""
        config = configparser.ConfigParser()
        try:
            config.read('config/config.ini')
            if config.has_section('playwright_mcp'):
                # Basic configuration
                self._server_mode = config.get('playwright_mcp', 'server_mode', fallback='always_run')
                
                # Performance configuration
                self._config = {
                    'enable_batch_execution': config.getboolean('playwright_mcp', 'enable_batch_execution', fallback=True),
                    'batch_threshold': config.getint('playwright_mcp', 'batch_threshold', fallback=3),
                    'snapshot_mode': config.get('playwright_mcp', 'snapshot_mode', fallback='final_only'),
                    'enable_metrics': config.getboolean('playwright_mcp', 'enable_metrics', fallback=True),
                    'shared_browser_context': config.getboolean('playwright_mcp', 'shared_browser_context', fallback=False),
                    'enable_session_persistence': config.getboolean('playwright_mcp', 'enable_session_persistence', fallback=True),
                    'session_dir': config.get('playwright_mcp', 'session_dir', fallback='.playwright-sessions'),
                }
                
                logger.info(f"🔧 MCP Server mode: {self._server_mode}")
                logger.info(f"⚡ Performance features: batch_execution={self._config['enable_batch_execution']}, "
                           f"snapshot_mode={self._config['snapshot_mode']}, "
                           f"metrics={self._config['enable_metrics']}")
            else:
                logger.warning("⚠️  No [playwright_mcp] section in config, using defaults")
                self._config = {
                    'enable_batch_execution': True,
                    'batch_threshold': 3,
                    'snapshot_mode': 'final_only',
                    'enable_metrics': True,
                    'shared_browser_context': False,
                    'enable_session_persistence': True,
                    'session_dir': '.playwright-sessions'
                }
        except Exception as e:
            logger.error(f"❌ Failed to load MCP config: {e}, using defaults")
            self._config = {
                'enable_batch_execution': True,
                'batch_threshold': 3,
                'snapshot_mode': 'final_only',
                'enable_metrics': True,
                'shared_browser_context': False,
                'enable_session_persistence': True,
                'session_dir': '.playwright-sessions'
            }
    
    def _get_snapshot_mode(self) -> SnapshotMode:
        """Convert string snapshot mode to enum"""
        mode_str = self._config.get('snapshot_mode', 'final_only')
        mode_map = {
            'always': SnapshotMode.ALWAYS,
            'never': SnapshotMode.NEVER,
            'final_only': SnapshotMode.FINAL_ONLY,
            'smart': SnapshotMode.SMART
        }
        return mode_map.get(mode_str, SnapshotMode.FINAL_ONLY)
    
    def get_client(self, headless: bool = True, browser: str = 'chromium') -> OptimizedMCPClient:
        """
        Get optimized MCP client instance based on server mode
        
        Args:
            headless: Run browser in headless mode
            browser: Browser type to use
            
        Returns:
            OptimizedMCPClient instance with performance enhancements
        """
        if self._server_mode == "always_run":
            return self._get_persistent_client(headless, browser)
        else:
            return self._create_new_client(headless, browser)
    
    def _get_persistent_client(self, headless: bool, browser: str) -> OptimizedMCPClient:
        """
        Get or create persistent optimized MCP client for 'always_run' mode
        
        Args:
            headless: Run browser in headless mode
            browser: Browser type to use
            
        Returns:
            Persistent OptimizedMCPClient instance
        """
        with self._lock:
            if self._client_instance is None:
                logger.info("🚀 Starting persistent optimized MCP server (always_run mode)")
                self._client_instance = self._create_new_client(headless, browser)
                logger.info("✅ Persistent optimized MCP server ready")
            return self._client_instance
    
    def _create_new_client(self, headless: bool, browser: str) -> OptimizedMCPClient:
        """
        Create new optimized MCP client instance
        
        Args:
            headless: Run browser in headless mode
            browser: Browser type to use
            
        Returns:
            New OptimizedMCPClient instance
        """
        snapshot_mode = self._get_snapshot_mode()
        enable_metrics = self._config.get('enable_metrics', True)
        
        client = OptimizedMCPClient(
            headless=headless,
            browser=browser,
            snapshot_mode=snapshot_mode,
            enable_metrics=enable_metrics
        )
        
        # Set batch threshold if batch execution is enabled
        if self._config.get('enable_batch_execution', True):
            client._batch_threshold = self._config.get('batch_threshold', 3)
        
        return client
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get server status and performance metrics
        
        Returns:
            Dictionary with status and metrics
        """
        status = {
            'server_mode': self._server_mode,
            'is_running': self._client_instance is not None,
            'configuration': self._config
        }
        
        if self._client_instance and self._config.get('enable_metrics', True):
            metrics = self._client_instance.get_metrics()
            if metrics:
                status['performance_metrics'] = metrics
        
        return status
    
    def reset_metrics(self):
        """Reset performance metrics"""
        if self._client_instance:
            self._client_instance.reset_metrics()
            logger.info("📊 MCP server metrics reset")
    
    def shutdown_server(self):
        """
        Shutdown the MCP server if running
        
        Only works in 'always_run' mode
        """
        with self._lock:
            if self._client_instance:
                logger.info("🛑 Shutting down MCP server...")
                
                # Show final metrics before shutdown
                if self._config.get('enable_metrics', True):
                    metrics = self._client_instance.get_metrics()
                    if metrics:
                        logger.info(f"📊 Final performance metrics: {metrics}")
                
                self._client_instance.close()
                self._client_instance = None
                logger.info("✅ MCP server shutdown complete")
            else:
                logger.warning("⚠️  No MCP server to shutdown")


# Global singleton instance
_manager = None
_manager_lock = threading.Lock()


def get_optimized_mcp_client(headless: bool = True, browser: str = 'chromium') -> OptimizedMCPClient:
    """
    Get optimized MCP client instance (convenience function)
    
    Args:
        headless: Run browser in headless mode
        browser: Browser type to use
        
    Returns:
        OptimizedMCPClient instance
    """
    global _manager
    with _manager_lock:
        if _manager is None:
            _manager = OptimizedMCPServerManager()
    return _manager.get_client(headless, browser)


def get_server_status() -> Dict[str, Any]:
    """Get MCP server status and metrics (convenience function)"""
    global _manager
    with _manager_lock:
        if _manager is None:
            _manager = OptimizedMCPServerManager()
    return _manager.get_status()


def reset_server_metrics():
    """Reset MCP server performance metrics (convenience function)"""
    global _manager
    with _manager_lock:
        if _manager is None:
            _manager = OptimizedMCPServerManager()
    _manager.reset_metrics()


def shutdown_optimized_server():
    """Shutdown optimized MCP server (convenience function)"""
    global _manager
    with _manager_lock:
        if _manager is None:
            return
    _manager.shutdown_server()
