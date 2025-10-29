"""
Engine Orchestrator
Manages and coordinates all browser automation engines
"""
from typing import Dict, Any, Tuple, Optional
import logging
import asyncio
import app.engines.playwright_mcp as playwright_mcp_codebase
import app.engines.browser_use as browser_use_codebase
from app.middleware.security import sanitize_error_message

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
    
    def get_engine_for_agents(self, engine_type: str, headless: bool):
        """
        Get engine instance for use by Planner/Generator/Healer agents
        
        Args:
            engine_type: 'playwright_mcp' or 'browser_use'
            headless: Run in headless mode
            
        Returns:
            Engine instance suitable for agent use
        """
        if engine_type == 'playwright_mcp':
            _, agent = self.get_playwright_engine(headless)
            return agent
        else:
            return self.get_browser_use_engine(headless)
    
    def execute_instruction_with_progress(self, instruction: str, engine_type: str, headless: bool, progress_callback=None, agent_mode: str = "direct", enable_agents: bool = True) -> Dict[str, Any]:
        """
        Execute an instruction with progress updates via callback
        
        Args:
            instruction: Natural language instruction
            engine_type: 'playwright_mcp' or 'browser_use'
            headless: Run in headless mode
            progress_callback: Optional callback function for progress updates
            agent_mode: Must be "direct" for playwright_mcp (ignored for browser_use)
            enable_agents: Whether to use Planner/Generator/Healer agents
            
        Returns:
            Execution result dictionary with playwright_code if agents enabled
        """
        return self.execute_instruction(instruction, engine_type, headless, progress_callback, agent_mode, enable_agents)
    
    def execute_instruction(self, instruction: str, engine_type: str, headless: bool, progress_callback=None, agent_mode: str = "direct", enable_agents: bool = True) -> Dict[str, Any]:
        """
        Execute an instruction using the specified engine with optional agent integration
        
        Args:
            instruction: Natural language instruction
            engine_type: 'playwright_mcp' or 'browser_use'
            headless: Run in headless mode
            progress_callback: Optional callback function for progress updates
            agent_mode: Must be "direct" for playwright_mcp (ignored for browser_use)
            enable_agents: Whether to use Planner/Generator/Healer agents
            
        Returns:
            Execution result dictionary with playwright_code and healed_code if agents enabled
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
        
        # Validate agent_mode for playwright_mcp - only 'direct' is supported
        if engine_type == 'playwright_mcp' and agent_mode != 'direct':
            logger.error(f"Invalid agent mode: {agent_mode}")
            return {
                'success': False,
                'error': f"Invalid agent mode: {agent_mode}",
                'message': "Only 'direct' mode is supported for Playwright MCP",
                'steps': [],
                'iterations': 0,
                'engine': engine_type,
                'headless': headless
            }
        
        # Initialize agent-generated code variables
        playwright_code = None
        healed_code = None
        
        # Run Planner → Generator agents before execution if enabled
        if enable_agents:
            try:
                logger.info("🎭 Running Planner → Generator agents before execution...")
                from app.agents.orchestrator import AgentOrchestrator
                
                # Get engine instance for agents
                engine_for_agents = self.get_engine_for_agents(engine_type, headless)
                agent_orch = AgentOrchestrator(engine_for_agents)
                
                # Generate playwright script using agents (async)
                playwright_code, plan = asyncio.run(
                    agent_orch.create_automation_script(instruction, {}, headless, use_cache=False, return_script_id=False)
                )
                
                logger.info(f"✅ Planner/Generator agents created script ({len(playwright_code)} chars)")
            except Exception as e:
                logger.warning(f"⚠️ Agent script generation failed (continuing with execution): {str(e)}")
                # Continue with execution even if agent generation fails
        
        result = None
        try:
            if engine_type == 'playwright_mcp':
                client, agent = self.get_playwright_engine(headless)
                
                try:
                    if not client.initialized:
                        logger.info("Initializing Playwright MCP client...")
                        client.initialize()
                    
                    result = agent.execute_instruction(instruction, mode=agent_mode)
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
                
                # Add generated playwright code to result if agents were used
                if playwright_code:
                    result['playwright_code'] = playwright_code
                    result['generated_code'] = playwright_code  # Legacy field name
                
                # If execution failed and agents are enabled, try to heal the script
                if not result.get('success') and enable_agents and playwright_code:
                    try:
                        logger.info("🎭 Execution failed, running Healer agent...")
                        from app.agents.orchestrator import AgentOrchestrator
                        
                        engine_for_agents = self.get_engine_for_agents(engine_type, headless)
                        agent_orch = AgentOrchestrator(engine_for_agents)
                        
                        # Heal the failed script (async)
                        error_msg = result.get('error', '') or result.get('message', '')
                        execution_logs = str(result.get('steps', []))
                        
                        healed_code = asyncio.run(
                            agent_orch.heal_failed_script(playwright_code, error_msg, execution_logs)
                        )
                        
                        result['healed_code'] = healed_code
                        logger.info(f"✅ Healer agent created fixed script ({len(healed_code)} chars)")
                    except Exception as heal_error:
                        logger.warning(f"⚠️ Healer agent failed: {str(heal_error)}")
                
                return result
            else:
                raise ValueError("Engine returned no result")
            
        except Exception as e:
            logger.error(f"Engine execution error ({engine_type}): {str(e)}", exc_info=True)
            user_message = sanitize_error_message(e)
            error_result = {
                'success': False,
                'error': 'Execution failed',
                'message': user_message,
                'steps': [],
                'iterations': 0,
                'engine': engine_type,
                'headless': headless
            }
            
            # Add generated code even on failure if agents were used
            if playwright_code:
                error_result['playwright_code'] = playwright_code
                error_result['generated_code'] = playwright_code
            
            # Try to heal the script even on exception if agents are enabled
            if enable_agents and playwright_code:
                try:
                    logger.info("🎭 Exception occurred, running Healer agent...")
                    from app.agents.orchestrator import AgentOrchestrator
                    
                    engine_for_agents = self.get_engine_for_agents(engine_type, headless)
                    agent_orch = AgentOrchestrator(engine_for_agents)
                    
                    healed_code = asyncio.run(
                        agent_orch.heal_failed_script(playwright_code, str(e), "")
                    )
                    
                    error_result['healed_code'] = healed_code
                    logger.info(f"✅ Healer agent created fixed script ({len(healed_code)} chars)")
                except Exception as heal_error:
                    logger.warning(f"⚠️ Healer agent failed: {str(heal_error)}")
            
            return error_result
    
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
