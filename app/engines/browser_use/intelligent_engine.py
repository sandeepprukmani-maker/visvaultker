"""
Intelligent Browser Use Engine
AI-enhanced browser automation engine with autonomous planning,
adaptive recovery, intelligent data extraction, and visual verification
"""
import logging
from typing import Dict, Any, Optional
from app.engines.browser_use.planner import TaskPlanner
from app.engines.browser_use.recovery_policy import RecoveryPolicyEngine
from app.engines.browser_use.semantic_extractor import SemanticExtractor
from app.engines.browser_use.visual_verifier import VisualVerifier
from app.engines.browser_use.memory_manager import MemoryManager
from app.engines.browser_use.engine_optimized import OptimizedBrowserUseEngine

logger = logging.getLogger(__name__)


class IntelligentBrowserUseEngine(OptimizedBrowserUseEngine):
    """
    AI-enhanced browser automation engine with autonomous planning,
    adaptive recovery, intelligent data extraction, and visual verification.
    
    Enhanced Features:
    - Autonomous task planning: Converts instructions into structured action graphs
    - Adaptive recovery: Automatically detects and recovers from failures
    - Semantic extraction: Uses LLM to extract structured data from HTML
    - Visual verification: Validates goals using screenshot analysis
    - Persistent memory: Learns from past executions to improve over time
    """

    def __init__(self, *args, **kwargs):
        """
        Initialize Intelligent Browser Use Engine
        
        Args:
            *args: Passed to OptimizedBrowserUseEngine
            **kwargs: Passed to OptimizedBrowserUseEngine
        """
        super().__init__(*args, **kwargs)
        
        # Initialize intelligent components
        self.task_planner = TaskPlanner(self.llm)
        self.recovery_policy = RecoveryPolicyEngine()
        self.semantic_extractor = SemanticExtractor(self.llm)
        self.visual_verifier = VisualVerifier(self.llm)
        self.memory = MemoryManager()
        
        logger.info("🧠 Intelligent Browser Use Engine initialized")
        logger.info("✨ Enhanced with: Planning, Recovery, Extraction, Verification, Memory")

    async def execute_intelligent(
        self, 
        instruction: str,
        use_planning: bool = True,
        use_recovery: bool = True,
        use_verification: bool = True,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Execute instruction with full intelligent capabilities
        
        Args:
            instruction: Natural language instruction
            use_planning: Whether to use autonomous planning
            use_recovery: Whether to use adaptive recovery
            use_verification: Whether to use visual verification
            **kwargs: Additional arguments passed to execution
            
        Returns:
            Dictionary with execution results and intelligence metrics
        """
        logger.info("🧠 Starting intelligent execution")
        logger.info(f"📋 Instruction: {instruction}")
        
        result = {
            "instruction": instruction,
            "plan": None,
            "execution_result": None,
            "verification": None,
            "recovery_attempts": 0,
            "intelligence_metrics": {}
        }
        
        try:
            # Step 1: Autonomous Planning (if enabled)
            if use_planning:
                plan = await self.task_planner.create_plan(instruction)
                self.memory.record_intent(instruction, plan)
                result["plan"] = plan
                logger.info(f"🧭 Plan created: {plan.get('goal', 'unknown goal')}")
                
                # Check if we have a successful plan from memory
                cached_plan = self.memory.get_plan(instruction)
                if cached_plan:
                    logger.info(f"🧠 Found successful plan in memory (reusing)")
                    plan = cached_plan
            else:
                plan = {
                    "goal": instruction,
                    "nodes": [{"id": 1, "action": "execute", "instruction": instruction}],
                    "edges": []
                }
                result["plan"] = plan
            
            # Step 2: Execute plan with recovery
            execution_success = False
            final_execution_result = None
            step_results = []
            
            # Check if plan has executable nodes
            nodes = plan.get("nodes", [])
            
            if use_planning and len(nodes) > 1:
                # Execute plan step by step with recovery
                logger.info(f"🔧 Executing {len(nodes)} planned steps")
                
                for idx, node in enumerate(nodes):
                    step_num = idx + 1
                    action = node.get("action", "unknown")
                    logger.info(f"📍 Step {step_num}/{len(nodes)}: {action}")
                    
                    step_success = False
                    retry_count = 0
                    max_retries = 3 if use_recovery else 1
                    
                    while retry_count < max_retries and not step_success:
                        try:
                            # Execute individual step based on action type
                            step_result = await self._execute_step(node, **kwargs)
                            step_success = step_result.get("success", False)
                            
                            if not step_success and use_recovery and retry_count < max_retries - 1:
                                # Apply recovery
                                recovery_info = await self.recovery_policy.handle_failure(node, step_result)
                                result["recovery_attempts"] += 1
                                
                                if recovery_info.get("recovered", False):
                                    logger.info(f"🔁 Retry {retry_count + 1}/{max_retries - 1}")
                                    retry_count += 1
                                else:
                                    break
                            else:
                                break
                                
                        except Exception as e:
                            logger.error(f"❌ Step {step_num} error: {e}")
                            step_result = {"success": False, "error": str(e)}
                            
                            if use_recovery and retry_count < max_retries - 1:
                                recovery_info = await self.recovery_policy.handle_failure(
                                    node, 
                                    {"error": str(e)}
                                )
                                result["recovery_attempts"] += 1
                                retry_count += 1
                            else:
                                break
                    
                    step_results.append({
                        "step": step_num,
                        "action": action,
                        "success": step_success,
                        "retries": retry_count
                    })
                    
                    # If step failed and not recovered, stop execution
                    if not step_success:
                        logger.warning(f"⚠️  Step {step_num} failed, stopping execution")
                        break
                
                # Overall success if all steps succeeded
                execution_success = all(s.get("success", False) for s in step_results)
                final_execution_result = {
                    "success": execution_success,
                    "steps": step_results,
                    "total_steps": len(nodes),
                    "completed_steps": len(step_results)
                }
            else:
                # Fallback to standard execution for simple instructions
                logger.info("🔧 Using standard execution (simple instruction or planning disabled)")
                execution_result = await self.execute_instruction(instruction, **kwargs)
                final_execution_result = execution_result
                execution_success = execution_result.get("success", False)
                
                # Apply recovery once if failed
                if not execution_success and use_recovery:
                    logger.warning("⚠️  Execution failed, attempting recovery")
                    recovery_info = await self.recovery_policy.handle_failure(
                        node={"action": "execute", "instruction": instruction},
                        result=execution_result
                    )
                    result["recovery_attempts"] += 1
                    
                    if recovery_info.get("recovered", False):
                        logger.info(f"✅ Recovery applied: {recovery_info['reason']}")
                        execution_result = await self.execute_instruction(instruction, **kwargs)
                        final_execution_result = execution_result
                        execution_success = execution_result.get("success", False)
            
            result["execution_result"] = final_execution_result
            result["step_results"] = step_results
            
            # Step 3: Visual Verification (if enabled and we have page context)
            verification_result = {"success": execution_success, "reasoning": "No verification performed"}
            
            if use_verification and "page" in kwargs and kwargs["page"] is not None:
                verification_result = await self.visual_verifier.validate_goal(
                    kwargs["page"], 
                    plan.get("goal", instruction)
                )
            elif use_verification:
                # Use execution result as verification
                verification_result = {
                    "success": execution_success,
                    "reasoning": "Verification based on execution result (no page context available)"
                }
            
            result["verification"] = verification_result
            
            # Step 4: Update Memory
            overall_success = execution_success and verification_result.get("success", True)
            self.memory.update_outcome(
                instruction, 
                success=overall_success,
                metadata={
                    "plan_steps": len(plan.get("nodes", [])),
                    "recovery_attempts": result["recovery_attempts"],
                    "verified": use_verification
                }
            )
            
            # Step 5: Collect Intelligence Metrics
            result["intelligence_metrics"] = {
                "planning_enabled": use_planning,
                "recovery_enabled": use_recovery,
                "verification_enabled": use_verification,
                "plan_complexity": len(plan.get("nodes", [])),
                "recovery_stats": self.recovery_policy.get_recovery_stats(),
                "verification_stats": self.visual_verifier.get_verification_stats(),
                "memory_stats": self.memory.get_stats(),
                "overall_success": overall_success
            }
            
            status_emoji = "✅" if overall_success else "❌"
            logger.info(f"{status_emoji} Intelligent execution completed")
            logger.info(f"📊 Recovery attempts: {result['recovery_attempts']}")
            logger.info(f"📊 Overall success: {overall_success}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Intelligent execution failed: {e}", exc_info=True)
            result["error"] = str(e)
            result["success"] = False
            self.memory.update_outcome(instruction, success=False, metadata={"error": str(e)})
            return result

    async def _execute_step(self, node: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """
        Execute a single plan step/node
        
        Args:
            node: Plan node with action and parameters
            **kwargs: Additional execution context
            
        Returns:
            Dictionary with step execution result
        """
        action = node.get("action", "execute")
        
        # For simple implementation, all actions delegate to the standard engine
        # In a full implementation, each action type would have specific handling
        
        if action == "navigate":
            url = node.get("url", "")
            instruction = f"Navigate to {url}"
        elif action == "type":
            selector = node.get("selector", "")
            value = node.get("value", "")
            instruction = f"Type '{value}' into {selector}"
        elif action == "click":
            selector = node.get("selector", "")
            instruction = f"Click on {selector}"
        elif action == "wait":
            duration = node.get("duration", 1)
            instruction = f"Wait for {duration} seconds"
        elif action == "verify":
            target = node.get("target_text", "")
            instruction = f"Verify that '{target}' is present"
        elif action == "extract":
            schema = node.get("schema", [])
            instruction = f"Extract data with schema: {schema}"
        elif action == "screenshot":
            instruction = "Take a screenshot"
        else:
            # Generic execution using the instruction field
            instruction = node.get("instruction", str(node))
        
        try:
            # Execute using the base engine
            result = await self.execute_instruction(instruction, **kwargs)
            return {
                "success": result.get("success", False),
                "result": result,
                "action": action
            }
        except Exception as e:
            logger.error(f"❌ Step execution failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "action": action
            }

    async def extract_data(
        self, 
        page, 
        schema: Optional[list] = None
    ) -> Dict[str, Any]:
        """
        Extract structured data from current page using semantic extraction
        
        Args:
            page: Playwright page object
            schema: Optional list of fields to extract
            
        Returns:
            Dictionary with extracted data
        """
        logger.info("🔍 Extracting data from page")
        data = await self.semantic_extractor.extract_from_page(page, schema)
        return {
            "success": True,
            "data": data,
            "count": len(data)
        }

    def get_intelligence_stats(self) -> Dict[str, Any]:
        """
        Get comprehensive statistics from all intelligent components
        
        Returns:
            Dictionary with all intelligence statistics
        """
        return {
            "recovery": self.recovery_policy.get_recovery_stats(),
            "verification": self.visual_verifier.get_verification_stats(),
            "memory": self.memory.get_stats(),
            "performance": self.get_performance_summary() if self.enable_advanced_features else {}
        }

    def reset_intelligence_stats(self):
        """Reset all intelligence statistics"""
        self.recovery_policy.reset_stats()
        self.visual_verifier.reset_stats()
        if self.enable_advanced_features:
            self.reset_metrics()
        logger.info("🔄 All intelligence statistics reset")
