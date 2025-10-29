"""
State Management for Complex Multi-Step Workflows
Preserves context and state across automation steps
"""
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class WorkflowState:
    """
    Manages state for complex multi-step automation workflows
    Preserves context, variables, and execution history
    """
    
    def __init__(self, workflow_id: Optional[str] = None, persist_to_disk: bool = False):
        """
        Initialize workflow state manager
        
        Args:
            workflow_id: Unique identifier for this workflow
            persist_to_disk: Save state to disk for recovery
        """
        self.workflow_id = workflow_id or f"workflow_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.persist_to_disk = persist_to_disk
        
        self.state: Dict[str, Any] = {}
        self.variables: Dict[str, Any] = {}
        self.execution_history: List[Dict[str, Any]] = []
        self.checkpoints: List[Dict[str, Any]] = []
        
        self.metadata = {
            "workflow_id": self.workflow_id,
            "created_at": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat(),
            "step_count": 0
        }
        
        if self.persist_to_disk:
            self.state_dir = Path("workflow_states")
            self.state_dir.mkdir(exist_ok=True)
            self.state_file = self.state_dir / f"{self.workflow_id}.json"
        
        logger.info(f"🔄 Workflow state initialized: {self.workflow_id}")
    
    def set_variable(self, key: str, value: Any):
        """
        Set a workflow variable
        
        Args:
            key: Variable name
            value: Variable value
        """
        self.variables[key] = value
        self.metadata["last_updated"] = datetime.now().isoformat()
        
        logger.debug(f"📝 Variable set: {key} = {value}")
        
        if self.persist_to_disk:
            self._save_to_disk()
    
    def get_variable(self, key: str, default: Any = None) -> Any:
        """
        Get a workflow variable
        
        Args:
            key: Variable name
            default: Default value if key doesn't exist
            
        Returns:
            Variable value or default
        """
        return self.variables.get(key, default)
    
    def set_state(self, key: str, value: Any):
        """
        Set a state value
        
        Args:
            key: State key
            value: State value
        """
        self.state[key] = value
        self.metadata["last_updated"] = datetime.now().isoformat()
        
        logger.debug(f"💾 State set: {key}")
        
        if self.persist_to_disk:
            self._save_to_disk()
    
    def get_state(self, key: str, default: Any = None) -> Any:
        """
        Get a state value
        
        Args:
            key: State key
            default: Default value if key doesn't exist
            
        Returns:
            State value or default
        """
        return self.state.get(key, default)
    
    def add_step(self, step_name: str, step_data: Dict[str, Any], success: bool = True):
        """
        Record a workflow step
        
        Args:
            step_name: Name of the step
            step_data: Data associated with the step
            success: Whether the step succeeded
        """
        step_record = {
            "step_number": self.metadata["step_count"] + 1,
            "step_name": step_name,
            "timestamp": datetime.now().isoformat(),
            "success": success,
            "data": step_data
        }
        
        self.execution_history.append(step_record)
        self.metadata["step_count"] += 1
        self.metadata["last_updated"] = datetime.now().isoformat()
        
        logger.info(f"✅ Step {self.metadata['step_count']} recorded: {step_name} (success: {success})")
        
        if self.persist_to_disk:
            self._save_to_disk()
    
    def create_checkpoint(self, checkpoint_name: str):
        """
        Create a checkpoint of current state
        
        Args:
            checkpoint_name: Name for this checkpoint
        """
        checkpoint = {
            "name": checkpoint_name,
            "timestamp": datetime.now().isoformat(),
            "state": self.state.copy(),
            "variables": self.variables.copy(),
            "step_count": self.metadata["step_count"]
        }
        
        self.checkpoints.append(checkpoint)
        logger.info(f"🔖 Checkpoint created: {checkpoint_name} (at step {self.metadata['step_count']})")
        
        if self.persist_to_disk:
            self._save_to_disk()
    
    def restore_checkpoint(self, checkpoint_name: str) -> bool:
        """
        Restore state from a checkpoint
        
        Args:
            checkpoint_name: Name of checkpoint to restore
            
        Returns:
            True if restored successfully, False if checkpoint not found
        """
        for checkpoint in reversed(self.checkpoints):
            if checkpoint["name"] == checkpoint_name:
                self.state = checkpoint["state"].copy()
                self.variables = checkpoint["variables"].copy()
                
                logger.info(f"♻️  Restored checkpoint: {checkpoint_name} (from step {checkpoint['step_count']})")
                
                if self.persist_to_disk:
                    self._save_to_disk()
                
                return True
        
        logger.warning(f"⚠️  Checkpoint not found: {checkpoint_name}")
        return False
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the workflow state
        
        Returns:
            Dictionary with state summary
        """
        return {
            "workflow_id": self.workflow_id,
            "metadata": self.metadata,
            "total_steps": self.metadata["step_count"],
            "total_checkpoints": len(self.checkpoints),
            "variable_count": len(self.variables),
            "state_keys": list(self.state.keys()),
            "success_rate": self._calculate_success_rate()
        }
    
    def _calculate_success_rate(self) -> float:
        """Calculate success rate of executed steps"""
        if not self.execution_history:
            return 100.0
        
        successful = sum(1 for step in self.execution_history if step["success"])
        return (successful / len(self.execution_history)) * 100
    
    def _save_to_disk(self):
        """Save state to disk"""
        try:
            state_data = {
                "workflow_id": self.workflow_id,
                "metadata": self.metadata,
                "state": self.state,
                "variables": self.variables,
                "execution_history": self.execution_history,
                "checkpoints": self.checkpoints
            }
            
            with open(self.state_file, 'w') as f:
                json.dump(state_data, f, indent=2)
            
            logger.debug(f"💾 State saved to: {self.state_file}")
        except Exception as e:
            logger.error(f"❌ Failed to save state: {str(e)}")
    
    @classmethod
    def load_from_disk(cls, workflow_id: str) -> Optional['WorkflowState']:
        """
        Load workflow state from disk
        
        Args:
            workflow_id: Workflow ID to load
            
        Returns:
            WorkflowState instance or None if not found
        """
        state_file = Path("workflow_states") / f"{workflow_id}.json"
        
        if not state_file.exists():
            logger.warning(f"⚠️  Workflow state not found: {workflow_id}")
            return None
        
        try:
            with open(state_file, 'r') as f:
                state_data = json.load(f)
            
            instance = cls(workflow_id=workflow_id, persist_to_disk=True)
            instance.metadata = state_data["metadata"]
            instance.state = state_data["state"]
            instance.variables = state_data["variables"]
            instance.execution_history = state_data["execution_history"]
            instance.checkpoints = state_data["checkpoints"]
            
            logger.info(f"📂 Workflow state loaded: {workflow_id}")
            return instance
            
        except Exception as e:
            logger.error(f"❌ Failed to load state: {str(e)}")
            return None
    
    def reset(self):
        """Reset workflow state"""
        self.state.clear()
        self.variables.clear()
        self.execution_history.clear()
        self.checkpoints.clear()
        self.metadata["step_count"] = 0
        self.metadata["last_updated"] = datetime.now().isoformat()
        
        logger.info(f"🔄 Workflow state reset: {self.workflow_id}")
        
        if self.persist_to_disk:
            self._save_to_disk()
