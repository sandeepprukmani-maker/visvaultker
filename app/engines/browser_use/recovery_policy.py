"""
Adaptive Error Handling
Detects, classifies, and recovers from execution failures using heuristics
"""
import asyncio
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class RecoveryPolicyEngine:
    """
    Detects, classifies, and recovers from execution failures using heuristics.
    """

    def __init__(self):
        """Initialize recovery policy engine"""
        self.recovery_attempts = 0
        self.recovery_history = []
        logger.info("🔁 Recovery Policy Engine initialized")

    async def handle_failure(self, node: dict, result: dict) -> dict:
        """
        Handle step failure with adaptive recovery
        
        Args:
            node: The failed node/step
            result: Result dictionary containing error information
            
        Returns:
            Dictionary with recovery information
        """
        error_type = str(result.get("error", "unknown")).lower()
        logger.warning(f"⚠️  Step failed: {node.get('action', 'unknown')} — error: {error_type}")

        recovery_info = {
            "recovered": False,
            "reason": "no recovery heuristic",
            "action_taken": None,
            "node_modified": False
        }

        # Timeout recovery - wait and retry
        if "timeout" in error_type or "timed out" in error_type:
            logger.info("🔁 Applying timeout recovery: waiting 3s before retry")
            await asyncio.sleep(3)
            recovery_info.update({
                "recovered": True,
                "reason": "waited and retry",
                "action_taken": "sleep_3s"
            })
            
        # Element not found - try alternative selectors
        elif "not found" in error_type or "no such element" in error_type:
            selector = node.get("selector", "")
            if selector:
                # Try converting ID selector to class selector
                if "#" in selector:
                    alt_selector = selector.replace("#", ".")
                    if alt_selector != selector:
                        node["selector"] = alt_selector
                        logger.info(f"🔁 Trying alternative selector: {alt_selector}")
                        recovery_info.update({
                            "recovered": True,
                            "reason": "used alternative selector (ID→class)",
                            "action_taken": "modified_selector",
                            "node_modified": True
                        })
                # Try more general selector
                elif ">" in selector or " " in selector:
                    parts = selector.split()
                    if len(parts) > 1:
                        alt_selector = parts[-1]  # Use last part
                        node["selector"] = alt_selector
                        logger.info(f"🔁 Trying simplified selector: {alt_selector}")
                        recovery_info.update({
                            "recovered": True,
                            "reason": "simplified selector",
                            "action_taken": "simplified_selector",
                            "node_modified": True
                        })
                        
        # Network errors - wait longer
        elif "network" in error_type or "connection" in error_type or "dns" in error_type:
            logger.info("🔁 Network error recovery: waiting 5s")
            await asyncio.sleep(5)
            recovery_info.update({
                "recovered": True,
                "reason": "network delay",
                "action_taken": "sleep_5s"
            })
            
        # Stale element - retry immediately
        elif "stale" in error_type or "detached" in error_type:
            logger.info("🔁 Stale element recovery: immediate retry")
            await asyncio.sleep(1)
            recovery_info.update({
                "recovered": True,
                "reason": "stale element retry",
                "action_taken": "sleep_1s"
            })
            
        # Rate limiting - exponential backoff
        elif "rate limit" in error_type or "429" in error_type or "too many requests" in error_type:
            wait_time = min(10, 2 ** self.recovery_attempts)
            logger.info(f"🔁 Rate limit recovery: waiting {wait_time}s")
            await asyncio.sleep(wait_time)
            recovery_info.update({
                "recovered": True,
                "reason": "rate limit backoff",
                "action_taken": f"sleep_{wait_time}s"
            })

        # Record recovery attempt
        self.recovery_attempts += 1
        self.recovery_history.append({
            "node": node.copy(),
            "error": error_type,
            "recovery": recovery_info
        })
        
        if recovery_info["recovered"]:
            logger.info(f"✅ Recovery applied: {recovery_info['reason']}")
        else:
            logger.warning(f"❌ No recovery strategy found for: {error_type}")
        
        return recovery_info

    def get_recovery_stats(self) -> Dict[str, Any]:
        """Get recovery statistics"""
        successful = sum(1 for h in self.recovery_history if h["recovery"]["recovered"])
        return {
            "total_attempts": self.recovery_attempts,
            "successful_recoveries": successful,
            "failed_recoveries": self.recovery_attempts - successful,
            "success_rate": successful / self.recovery_attempts if self.recovery_attempts > 0 else 0
        }

    def reset_stats(self):
        """Reset recovery statistics"""
        self.recovery_attempts = 0
        self.recovery_history.clear()
        logger.info("🔄 Recovery stats reset")
