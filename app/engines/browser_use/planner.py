"""
Autonomous Task Planner
Converts user instructions into structured, goal-driven action graphs using an LLM
"""
import json
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


class TaskPlanner:
    """
    Converts user instructions into structured, goal-driven action graphs
    using an LLM.
    """

    def __init__(self, llm):
        """
        Initialize task planner
        
        Args:
            llm: Language model for planning
        """
        self.llm = llm
        logger.info("🧭 Task Planner initialized")

    async def create_plan(self, instruction: str) -> Dict[str, Any]:
        """
        Create a structured plan from a user instruction
        
        Args:
            instruction: User's natural language instruction
            
        Returns:
            Dictionary with goal, nodes, and edges
        """
        prompt = f"""
You are a web automation strategist.
Convert this instruction into a structured, step-by-step plan:
"{instruction}"

Output JSON only, with fields:
{{
    "goal": "high-level goal",
    "nodes": [
        {{"id": 1, "action": "navigate", "url": "..."}},
        {{"id": 2, "action": "type", "selector": "...", "value": "..."}},
        {{"id": 3, "action": "click", "selector": "..."}},
        {{"id": 4, "action": "verify", "target_text": "..."}}
    ],
    "edges": [[1,2],[2,3],[3,4]]
}}

Action types: navigate, type, click, wait, verify, extract, screenshot
Keep the plan concise but complete.
"""
        response_text = ""
        try:
            logger.info(f"🧭 Creating plan for: {instruction[:100]}")
            response = await self.llm.ainvoke(prompt)
            
            # Try to parse JSON from response
            response_text = str(response)
            
            # Extract JSON if wrapped in markdown or text
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()
            elif "```" in response_text:
                json_start = response_text.find("```") + 3
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()
            
            plan = json.loads(response_text)
            logger.info(f"✅ Plan created with {len(plan.get('nodes', []))} steps")
            return plan
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ Failed to parse plan JSON: {e}")
            logger.debug(f"Response was: {response_text[:500]}")
            return {
                "goal": instruction, 
                "nodes": [{"id": 1, "action": "execute", "instruction": instruction}], 
                "edges": []
            }
        except Exception as e:
            logger.error(f"❌ Plan creation failed: {e}")
            return {
                "goal": instruction, 
                "nodes": [{"id": 1, "action": "execute", "instruction": instruction}], 
                "edges": []
            }
