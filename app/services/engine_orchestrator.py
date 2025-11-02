"""
Engine Orchestrator
Manages and coordinates all browser automation engines with enhanced validation and healing
"""
from typing import Dict, Any, Tuple, Optional
import logging
import asyncio
import app.engines.playwright_mcp as playwright_mcp_codebase
import app.engines.browser_use as browser_use_codebase
from app.middleware.security import sanitize_error_message
from app.utils.prompt_enhancer import enhance_instruction_with_knowledge
from app.utils.website_learning import learn_from_execution
from app.services.intelligent_coordinator import IntelligentCoordinator
# Code generation imports removed - using pure execution mode only

logger = logging.getLogger(__name__)


class EngineOrchestrator:
    """
    Orchestrates browser automation engines (Playwright MCP and Browser-Use)
    Handles engine instantiation, caching, and execution delegation
    """
    
    def __init__(self):
        """Initialize the orchestrator with empty engine caches"""
        self.playwright_engines = {}
        self.browser_use_engines = {}
        self.intelligent_coordinator = IntelligentCoordinator()
        logger.info("🧠 Intelligent Coordinator enabled - ALL automations will be analyzed")
    
    def get_playwright_engine(self, headless: bool) -> Tuple[Any, Any]:
        """
        Get or create Playwright MCP engine instance
        
        Args:
            headless: Run in headless mode
            
        Returns:
            Tuple of (mcp_client, browser_agent)
        """
        if headless not in self.playwright_engines:
            mcp_client, browser_agent = playwright_mcp_codebase.create_engine(headless=headless)
            self.playwright_engines[headless] = (mcp_client, browser_agent)
        
        return self.playwright_engines[headless]
    
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
            engine_type: 'playwright_mcp' or 'browser_use'
            headless: Run in headless mode
            progress_callback: Optional callback function for progress updates
            
        Returns:
            Execution result dictionary
        """
        return self.execute_instruction(instruction, engine_type, headless, progress_callback)
    
    def execute_instruction(self, instruction: str, engine_type: str, headless: bool, progress_callback=None) -> Dict[str, Any]:
        """
        Execute an instruction using the specified engine with intelligent coordination
        
        Engine Behavior:
        - 'playwright_mcp': Direct execution with Playwright MCP
        - 'browser_use': Direct execution with Browser-Use
        
        Args:
            instruction: Natural language instruction
            engine_type: 'playwright_mcp' or 'browser_use'
            headless: Run in headless mode
            progress_callback: Optional callback function for progress updates
            
        Returns:
            Dict with execution results
        """
        valid_engines = ['playwright_mcp', 'browser_use']
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
        
        # Store original instruction
        original_instruction = instruction
        
        # STEP 1: Intelligent Analysis
        logger.info("="*80)
        logger.info("🧠 INTELLIGENT AUTOMATION ANALYSIS")
        logger.info("="*80)
        
        analysis = self.intelligent_coordinator.analyze_instruction(instruction)
        
        # Log analysis results
        logger.info(f"📊 Task Complexity: {analysis['complexity'].upper()}")
        logger.info(f"🎯 Task Type: {analysis['task_type']}")
        logger.info(f"📋 Subtasks: {analysis['subtask_count']}")
        logger.info(f"⚙️  Recommended Engine: {analysis['recommended_engine']}")
        logger.info(f"🌡️  Recommended Temperature: {analysis['recommended_temperature']}")
        logger.info(f"📏 Estimated Steps: {analysis['estimated_steps']}")
        if analysis['risk_factors']:
            logger.warning(f"⚠️  Risk Factors: {', '.join(analysis['risk_factors'])}")
        
        # STEP 2: Apply intelligent recommendations
        # Note: Auto-swapping disabled - respecting user's engine choice
        if analysis['recommended_engine'] != engine_type:
            logger.info(f"ℹ️  Recommendation: {analysis['recommended_engine']} might be better suited for {analysis['task_type']} tasks")
            logger.info(f"   Using your selection: {engine_type}")
        
        # STEP 3: Enhance instruction with intelligent guidance
        instruction = self.intelligent_coordinator.enhance_instruction(instruction, analysis)
        
        # STEP 4: Enhance with learned website knowledge
        instruction, target_url = enhance_instruction_with_knowledge(instruction)
        
        logger.info("="*80)
        
        # Direct execution only - no code generation
        logger.info("🚀 Direct execution mode - no code generation")
        
        result = None
        try:
            if engine_type == 'playwright_mcp':
                # Direct execution with Playwright MCP
                client, agent = self.get_playwright_engine(headless)
                
                try:
                    if not client.initialized:
                        logger.info("Initializing Playwright MCP client...")
                        client.initialize()
                    
                    # Execute the automation directly
                    logger.info("🎭 Executing automation with Playwright MCP...")
                    result = agent.execute_instruction(instruction, mode="direct", progress_callback=progress_callback)
                except Exception as e:
                    logger.error(f"Playwright MCP error: {str(e)}, attempting to reinitialize")
                    self._reset_playwright_engine(headless)
                    raise
                
            elif engine_type == 'browser_use':
                engine = self.get_browser_use_engine(headless)
                result = engine.execute_instruction_sync(instruction, progress_callback=progress_callback, save_screenshot=True)
            
            if result is not None:
                result['engine'] = engine_type
                result['headless'] = headless
                
                # Learn from this execution if we have a target URL
                if target_url:
                    try:
                        steps = result.get('steps', []) or result.get('history', [])
                        success = result.get('success', False)
                        learn_from_execution(target_url, original_instruction, steps, success)
                    except Exception as learn_error:
                        logger.error(f"Failed to learn from execution: {learn_error}")
                
                # No code generation or healing - just return execution results
                
                return result
            else:
                raise ValueError("Engine returned no result")
            
        except Exception as e:
            logger.error(f"Engine execution error ({engine_type}): {str(e)}", exc_info=True)
            user_message = sanitize_error_message(e)
            
            # Learn from failure too if we have a target URL
            if target_url:
                try:
                    learn_from_execution(target_url, original_instruction, [], False)
                except Exception as learn_error:
                    logger.error(f"Failed to learn from failure: {learn_error}")
            
            return {
                'success': False,
                'error': 'Execution failed',
                'message': user_message,
                'steps': [],
                'iterations': 0,
                'engine': engine_type,
                'headless': headless
            }
    
    def _reset_playwright_engine(self, headless: bool):
        """
        Reset Playwright engine if it crashes or becomes unresponsive
        
        Args:
            headless: Headless mode setting
        """
        if headless in self.playwright_engines:
            logger.warning(f"Resetting Playwright engine (headless={headless})")
            try:
                client, _ = self.playwright_engines[headless]
                if hasattr(client, 'cleanup'):
                    client.cleanup()
            except Exception as e:
                logger.error(f"Error during Playwright cleanup: {str(e)}")
            finally:
                del self.playwright_engines[headless]
    
    def get_tools(self, engine_type: str) -> list:
        """
        Get available tools for the specified engine
        
        Args:
            engine_type: 'playwright_mcp' or 'browser_use'
            
        Returns:
            List of available tools
        """
        if engine_type == 'playwright_mcp':
            client, _ = self.get_playwright_engine(headless=True)
            
            if not client.initialized:
                client.initialize()
            
            return client.list_tools()
        else:
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
            if engine_type == 'playwright_mcp':
                self._reset_playwright_engine(headless)
            elif engine_type == 'browser_use':
                # Reset browser_use engine by removing it from cache
                # This forces a fresh engine on next request
                if headless in self.browser_use_engines:
                    logger.info(f"Removing browser_use engine from cache (headless={headless})")
                    del self.browser_use_engines[headless]
        except Exception as e:
            logger.error(f"Error during timeout cleanup: {str(e)}")
    
    
    def reset_agent(self, engine_type: str, headless: bool = True):
        """
        Reset the conversation history for the specified engine
        
        Args:
            engine_type: 'playwright_mcp' or 'browser_use'
            headless: Headless mode (for Playwright MCP)
        """
        if engine_type == 'playwright_mcp':
            _, agent = self.get_playwright_engine(headless)
            agent.reset_conversation()
