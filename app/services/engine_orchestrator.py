"""
Engine Orchestrator
Manages and coordinates browser automation engines
"""
from typing import Dict, Any, Optional
import logging
import asyncio
import configparser
from pathlib import Path
import app.engines.browser_use as browser_use_codebase
from app.middleware.security import sanitize_error_message

logger = logging.getLogger(__name__)


class EngineOrchestrator:
    """
    Orchestrates browser automation engines (Browser-Use and Playwright MCP)
    Handles engine instantiation, caching, and execution delegation
    """
    
    def __init__(self):
        """Initialize the orchestrator with empty engine caches"""
        self.browser_use_engines = {}
        self.playwright_mcp_engine = None
        self.config = self._load_config()
        
    def _load_config(self) -> configparser.ConfigParser:
        """Load configuration from config.ini"""
        config = configparser.ConfigParser()
        config_path = Path(__file__).parent.parent.parent / 'config' / 'config.ini'
        
        if config_path.exists():
            config.read(config_path)
        
        return config
    
    def get_browser_use_engine(self, headless: bool):
        """
        Get or create Browser-Use engine instance
        Caches instances per headless mode for better performance
        
        Args:
            headless: Run in headless mode
            
        Returns:
            BrowserUseEngine instance
        """
        if headless not in self.browser_use_engines:
            self.browser_use_engines[headless] = browser_use_codebase.create_engine(headless=headless)
        
        return self.browser_use_engines[headless]
    
    def get_playwright_mcp_engine(self):
        """
        Get or create Playwright MCP engine instance
        
        Returns:
            PlaywrightMCPEngine instance
        """
        if self.playwright_mcp_engine is None:
            from app.engines.playwright_mcp import PlaywrightMCPEngine
            self.playwright_mcp_engine = PlaywrightMCPEngine()
        
        return self.playwright_mcp_engine
    
    
    def execute_instruction_with_progress(self, instruction: str, engine_type: str, headless: bool, progress_callback=None) -> Dict[str, Any]:
        """
        Execute an instruction with progress updates via callback
        
        Args:
            instruction: Natural language instruction
            engine_type: 'browser_use' only
            headless: Run in headless mode
            progress_callback: Optional callback function for progress updates
            
        Returns:
            Execution result dictionary
        """
        return self.execute_instruction(instruction, engine_type, headless, progress_callback)
    
    def execute_instruction(self, instruction: str, engine_type: str, headless: bool, progress_callback=None) -> Dict[str, Any]:
        """
        Execute an instruction using the specified engine
        
        Args:
            instruction: Natural language instruction
            engine_type: 'browser_use' or 'playwright_mcp'
            headless: Run in headless mode (only for browser_use)
            progress_callback: Optional callback function for progress updates
            
        Returns:
            Dict with execution results
        """
        valid_engines = ['browser_use', 'playwright_mcp']
        if engine_type not in valid_engines:
            logger.error(f"Invalid engine type: {engine_type}")
            return {
                'success': False,
                'error': f"Invalid engine type: {engine_type}. Must be one of: {', '.join(valid_engines)}",
                'steps': [],
                'iterations': 0,
                'engine': engine_type,
                'headless': headless
            }
        
        # Execute with the appropriate engine
        if engine_type == 'browser_use':
            return self._execute_browser_use(instruction, headless, progress_callback)
        elif engine_type == 'playwright_mcp':
            return self._execute_playwright_mcp(instruction, headless, progress_callback)
    
    def _execute_browser_use(self, instruction: str, headless: bool, progress_callback=None) -> Dict[str, Any]:
        """Execute instruction using Browser-Use engine"""
        logger.info("🚀 Executing automation with Browser-Use engine")
        
        result = None
        try:
            engine = self.get_browser_use_engine(headless)
            result = engine.execute_instruction_sync(instruction, progress_callback=progress_callback, save_screenshot=True)
            
            if result is not None:
                result['engine'] = 'browser_use'
                result['headless'] = headless
                return result
            else:
                raise ValueError("Engine returned no result")
            
        except Exception as e:
            logger.error(f"Browser-Use engine execution error: {str(e)}", exc_info=True)
            user_message = sanitize_error_message(e)
            
            return {
                'success': False,
                'error': 'Execution failed',
                'message': user_message,
                'steps': [],
                'iterations': 0,
                'engine': 'browser_use',
                'headless': headless
            }
    
    def _execute_playwright_mcp(self, instruction: str, headless: bool, progress_callback=None) -> Dict[str, Any]:
        """Execute instruction using Playwright MCP engine"""
        logger.info("🚀 Executing automation with Playwright MCP engine")
        
        try:
            engine = self.get_playwright_mcp_engine()
            
            # Run async task in event loop
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(engine.run_task(instruction, headless=headless))
            finally:
                loop.close()
            
            if result.get('success'):
                return {
                    'success': True,
                    'result': result.get('result', {}),
                    'message': result['result'].get('message', 'Task completed'),
                    'trace': result['result'].get('trace', []),
                    'steps': len(result['result'].get('trace', [])),
                    'iterations': len([t for t in result['result'].get('trace', []) if t.get('type') == 'tool_call']),
                    'engine': 'playwright_mcp',
                    'headless': headless
                }
            else:
                return {
                    'success': False,
                    'error': result.get('error', 'Unknown error'),
                    'message': result.get('error', 'Task execution failed'),
                    'steps': [],
                    'iterations': 0,
                    'engine': 'playwright_mcp',
                    'headless': headless
                }
            
        except Exception as e:
            logger.error(f"Playwright MCP engine execution error: {str(e)}", exc_info=True)
            user_message = sanitize_error_message(e)
            
            return {
                'success': False,
                'error': 'Execution failed',
                'message': user_message,
                'steps': [],
                'iterations': 0,
                'engine': 'playwright_mcp',
                'headless': headless
            }
    
    def get_tools(self, engine_type: str) -> list:
        """
        Get available tools for the specified engine
        
        Args:
            engine_type: 'browser_use' or 'playwright_mcp'
            
        Returns:
            List of available tools
        """
        if engine_type == 'browser_use':
            return [
                {'name': 'browser_use_agent', 'description': 'AI-powered browser automation'}
            ]
        elif engine_type == 'playwright_mcp':
            return [
                {'name': 'playwright_mcp_agent', 'description': 'AI-powered browser automation using Playwright MCP'}
            ]
        return []
    
    def cleanup_after_timeout(self, engine_type: str, headless: bool):
        """
        Clean up resources after a timed-out execution
        
        Args:
            engine_type: Engine that was executing when timeout occurred
            headless: Headless mode setting
        """
        logger.warning(f"Cleaning up after timeout for {engine_type} (headless={headless})")
        
        try:
            if engine_type == 'browser_use':
                # Reset browser_use engine by removing it from cache
                # This forces a fresh engine on next request
                if headless in self.browser_use_engines:
                    logger.info(f"Removing browser_use engine from cache (headless={headless})")
                    del self.browser_use_engines[headless]
            elif engine_type == 'playwright_mcp':
                # Reset Playwright MCP engine
                self.playwright_mcp_engine = None
        except Exception as e:
            logger.error(f"Error during timeout cleanup: {str(e)}")
    
    def reset_agent(self, engine_type: str, headless: bool = True):
        """
        Reset the conversation history for the specified engine
        
        Args:
            engine_type: 'browser_use' or 'playwright_mcp'
            headless: Headless mode setting
        """
        logger.info(f"Reset requested for {engine_type} engine")
        
        if engine_type == 'playwright_mcp':
            # Reset Playwright MCP engine
            self.playwright_mcp_engine = None
