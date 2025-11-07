"""
Engine Orchestrator
Manages and coordinates browser automation engines
"""
from typing import Dict, Any, Optional
import logging
import app.engines.browser_use as browser_use_codebase
from app.middleware.security import sanitize_error_message

logger = logging.getLogger(__name__)


class EngineOrchestrator:
    """
    Orchestrates browser automation engines (Browser-Use)
    Handles engine instantiation, caching, and execution delegation
    """
    
    def __init__(self):
        """Initialize the orchestrator with empty engine caches"""
        self.browser_use_engines = {}
    
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
        Execute an instruction using the Browser-Use engine
        
        Args:
            instruction: Natural language instruction
            engine_type: 'browser_use' only
            headless: Run in headless mode
            progress_callback: Optional callback function for progress updates
            
        Returns:
            Dict with execution results
        """
        valid_engines = ['browser_use']
        if engine_type not in valid_engines:
            logger.error(f"Invalid engine type: {engine_type}")
            return {
                'success': False,
                'error': f"Invalid engine type: {engine_type}. Must be: browser_use",
                'steps': [],
                'iterations': 0,
                'engine': engine_type,
                'headless': headless
            }
        
        logger.info("🚀 Executing automation with Browser-Use engine")
        
        result = None
        try:
            engine = self.get_browser_use_engine(headless)
            result = engine.execute_instruction_sync(instruction, progress_callback=progress_callback, save_screenshot=True)
            
            if result is not None:
                result['engine'] = engine_type
                result['headless'] = headless
                return result
            else:
                raise ValueError("Engine returned no result")
            
        except Exception as e:
            logger.error(f"Engine execution error ({engine_type}): {str(e)}", exc_info=True)
            user_message = sanitize_error_message(e)
            
            return {
                'success': False,
                'error': 'Execution failed',
                'message': user_message,
                'steps': [],
                'iterations': 0,
                'engine': engine_type,
                'headless': headless
            }
    
    def get_tools(self, engine_type: str) -> list:
        """
        Get available tools for the specified engine
        
        Args:
            engine_type: 'browser_use' only
            
        Returns:
            List of available tools
        """
        return [
            {'name': 'browser_use_agent', 'description': 'AI-powered browser automation'}
        ]
    
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
        except Exception as e:
            logger.error(f"Error during timeout cleanup: {str(e)}")
    
    def reset_agent(self, engine_type: str, headless: bool = True):
        """
        Reset the conversation history for the browser_use engine
        
        Args:
            engine_type: 'browser_use' only
            headless: Headless mode setting
        """
        # Browser-use engine doesn't maintain conversation history
        logger.info(f"Reset requested for {engine_type} engine")
