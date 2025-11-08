"""
Persistent Learning Layer
Remembers past successes, selectors, and site patterns for re-use
"""
import json
import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class MemoryManager:
    """
    Remembers past successes, selectors, and site patterns for re-use.
    """

    def __init__(self, memory_file: str = "browser_memory.json"):
        """
        Initialize memory manager
        
        Args:
            memory_file: Path to memory file
        """
        # Store in automation_outputs directory
        output_dir = Path("automation_outputs")
        output_dir.mkdir(exist_ok=True)
        
        self.memory_file = output_dir / memory_file
        self.data = self._load()
        logger.info(f"🧠 Memory Manager initialized (file: {self.memory_file})")

    def _load(self) -> Dict[str, Any]:
        """Load memory from disk"""
        if self.memory_file.exists():
            try:
                with open(self.memory_file, "r") as f:
                    data = json.load(f)
                    logger.info(f"📖 Loaded memory: {len(data)} entries")
                    return data
            except Exception as e:
                logger.error(f"❌ Failed to load memory: {e}")
                return {}
        return {}

    def _save(self):
        """Save memory to disk"""
        try:
            with open(self.memory_file, "w") as f:
                json.dump(self.data, f, indent=2)
            logger.debug(f"💾 Memory saved: {len(self.data)} entries")
        except Exception as e:
            logger.error(f"❌ Failed to save memory: {e}")

    def record_intent(self, instruction: str, plan: Dict[str, Any]):
        """
        Record a new instruction and its plan
        
        Args:
            instruction: User instruction
            plan: Execution plan
        """
        key = self._normalize_instruction(instruction)
        
        if key not in self.data:
            self.data[key] = {
                "instruction": instruction,
                "plan": plan,
                "successes": 0,
                "failures": 0,
                "first_seen": datetime.now().isoformat(),
                "last_used": datetime.now().isoformat(),
                "total_executions": 0
            }
        else:
            self.data[key]["last_used"] = datetime.now().isoformat()
            
        self._save()
        logger.info(f"🧠 Recorded intent: {instruction[:50]}")

    def update_outcome(self, instruction: str, success: bool = True, metadata: Optional[Dict] = None):
        """
        Update execution outcome for an instruction
        
        Args:
            instruction: User instruction
            success: Whether execution was successful
            metadata: Optional additional metadata
        """
        key = self._normalize_instruction(instruction)
        
        if key in self.data:
            self.data[key]["total_executions"] += 1
            if success:
                self.data[key]["successes"] += 1
            else:
                self.data[key]["failures"] += 1
            
            self.data[key]["last_used"] = datetime.now().isoformat()
            
            # Store metadata if provided
            if metadata:
                if "execution_history" not in self.data[key]:
                    self.data[key]["execution_history"] = []
                self.data[key]["execution_history"].append({
                    "timestamp": datetime.now().isoformat(),
                    "success": success,
                    "metadata": metadata
                })
                # Keep only last 10 executions
                self.data[key]["execution_history"] = self.data[key]["execution_history"][-10:]
            
            self._save()
            logger.info(f"✅ Updated outcome: {instruction[:50]} - Success: {success}")
        else:
            logger.warning(f"⚠️  Instruction not found in memory: {instruction[:50]}")

    def get_plan(self, instruction: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve stored plan for an instruction
        
        Args:
            instruction: User instruction
            
        Returns:
            Stored plan if found, None otherwise
        """
        key = self._normalize_instruction(instruction)
        entry = self.data.get(key)
        
        if entry and entry.get("successes", 0) > 0:
            logger.info(f"🧠 Retrieved successful plan for: {instruction[:50]}")
            return entry.get("plan")
        
        return None

    def get_success_rate(self, instruction: str) -> float:
        """
        Get success rate for an instruction
        
        Args:
            instruction: User instruction
            
        Returns:
            Success rate (0.0 to 1.0)
        """
        key = self._normalize_instruction(instruction)
        entry = self.data.get(key)
        
        if not entry:
            return 0.0
        
        total = entry.get("total_executions", 0)
        if total == 0:
            return 0.0
        
        successes = entry.get("successes", 0)
        return successes / total

    def get_stats(self) -> Dict[str, Any]:
        """Get memory statistics"""
        total_entries = len(self.data)
        total_successes = sum(e.get("successes", 0) for e in self.data.values())
        total_failures = sum(e.get("failures", 0) for e in self.data.values())
        total_executions = sum(e.get("total_executions", 0) for e in self.data.values())
        
        return {
            "total_entries": total_entries,
            "total_executions": total_executions,
            "total_successes": total_successes,
            "total_failures": total_failures,
            "overall_success_rate": total_successes / total_executions if total_executions > 0 else 0.0
        }

    def clear_memory(self):
        """Clear all memory"""
        self.data.clear()
        self._save()
        logger.info("🗑️  Memory cleared")

    def _normalize_instruction(self, instruction: str) -> str:
        """Normalize instruction for consistent keying"""
        # Convert to lowercase and strip whitespace
        return instruction.lower().strip()
