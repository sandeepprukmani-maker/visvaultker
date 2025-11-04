"""
Workflow Orchestration Engine
Chains multiple tasks with data passing and conditional logic
"""

from typing import Dict, List, Any, Optional
from backend.task_executor import TaskExecutor
from backend.browser_engine import BrowserEngine
from datetime import datetime
import asyncio
import json

class WorkflowOrchestrator:
    def __init__(self, task_executor: TaskExecutor):
        self.task_executor = task_executor
        self.workflow_logs: Dict[str, List[str]] = {}
    
    async def execute_workflow(
        self,
        workflow_id: str,
        workflow_data: Dict[str, Any],
        tasks: List[Dict[str, Any]],
        profiles: Dict[str, Dict[str, Any]],
        parameters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute a complete workflow
        
        Args:
            workflow_id: Workflow identifier
            workflow_data: Workflow configuration
            tasks: List of tasks to execute in order
            profiles: Website profiles for each task
            parameters: Global workflow parameters
        
        Returns:
            Workflow execution result
        """
        execution_id = f"workflow_{workflow_id}_{int(datetime.utcnow().timestamp())}"
        self.workflow_logs[execution_id] = []
        
        self._log(execution_id, f"Starting workflow: {workflow_data.get('title')}")
        
        # Execution context (stores data passed between tasks)
        execution_context = parameters or {}
        task_results = []
        
        # Get execution order and data mapping
        execution_order = workflow_data.get('execution_order', [])
        data_mapping = workflow_data.get('data_mapping', {})
        conditional_logic = workflow_data.get('conditional_logic', {})
        
        try:
            # Execute tasks in order
            for task_idx, task_data in enumerate(tasks):
                task_id = task_data['id']
                profile_id = task_data['website_profile_id']
                profile_data = profiles.get(profile_id, {})
                
                # Check conditional logic
                if self._should_skip_task(task_id, conditional_logic, execution_context):
                    self._log(execution_id, f"Skipping task {task_idx + 1}: {task_data.get('title')} (condition not met)")
                    continue
                
                self._log(execution_id, f"Executing task {task_idx + 1}/{len(tasks)}: {task_data.get('title')}")
                
                # Prepare task parameters from previous task outputs
                task_parameters = self._prepare_task_parameters(
                    task_id,
                    data_mapping,
                    execution_context,
                    task_results
                )
                
                # Execute task
                result = await self.task_executor.execute_task(
                    task_id,
                    task_data,
                    profile_data,
                    parameters=task_parameters
                )
                
                task_results.append({
                    'task_id': task_id,
                    'task_title': task_data.get('title'),
                    'result': result,
                    'order': task_idx
                })
                
                # Update execution context with task output
                if result.get('status') == 'success':
                    extracted_data = result.get('extracted_data', {})
                    execution_context[f"task_{task_id}_output"] = extracted_data
                    self._log(execution_id, f"Task {task_idx + 1} completed successfully")
                else:
                    error = result.get('error', 'Unknown error')
                    self._log(execution_id, f"Task {task_idx + 1} failed: {error}")
                    
                    # Check if workflow should continue on error
                    if not workflow_data.get('continue_on_error', False):
                        self._log(execution_id, "Stopping workflow due to task failure")
                        break
            
            # Determine overall status
            failed_tasks = [r for r in task_results if r['result'].get('status') == 'failed']
            overall_status = 'success' if len(failed_tasks) == 0 else 'partial_success' if len(failed_tasks) < len(task_results) else 'failed'
            
            self._log(execution_id, f"Workflow completed with status: {overall_status}")
            
            return {
                'execution_id': execution_id,
                'workflow_id': workflow_id,
                'status': overall_status,
                'task_results': task_results,
                'execution_context': execution_context,
                'logs': self.workflow_logs[execution_id],
                'completed_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            self._log(execution_id, f"Workflow error: {str(e)}")
            
            return {
                'execution_id': execution_id,
                'workflow_id': workflow_id,
                'status': 'failed',
                'error': str(e),
                'task_results': task_results,
                'logs': self.workflow_logs[execution_id],
                'completed_at': datetime.utcnow().isoformat()
            }
    
    def _should_skip_task(
        self,
        task_id: str,
        conditional_logic: Dict[str, Any],
        execution_context: Dict[str, Any]
    ) -> bool:
        """Check if task should be skipped based on conditional logic"""
        
        if not conditional_logic:
            return False
        
        task_conditions = conditional_logic.get(task_id)
        if not task_conditions:
            return False
        
        # Simple condition evaluation
        condition_type = task_conditions.get('type')
        
        if condition_type == 'skip_if_empty':
            field = task_conditions.get('field')
            value = execution_context.get(field)
            return not value or (isinstance(value, (list, dict)) and len(value) == 0)
        
        elif condition_type == 'skip_if_failed':
            dependent_task = task_conditions.get('dependent_task')
            dependent_output = execution_context.get(f"task_{dependent_task}_output")
            return dependent_output is None
        
        return False
    
    def _prepare_task_parameters(
        self,
        task_id: str,
        data_mapping: Dict[str, Any],
        execution_context: Dict[str, Any],
        task_results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Prepare parameters for task from previous task outputs"""
        
        parameters = {}
        
        # Get data mapping for this task
        task_mapping = data_mapping.get(task_id, {})
        
        for param_name, source in task_mapping.items():
            if source.startswith('task_'):
                # Extract from previous task output
                value = execution_context.get(source)
                if value:
                    parameters[param_name] = value
            elif source in execution_context:
                # Extract from global context
                parameters[param_name] = execution_context[source]
        
        return parameters
    
    def _log(self, execution_id: str, message: str) -> None:
        """Add log entry"""
        timestamp = datetime.utcnow().isoformat()
        log_entry = f"[{timestamp}] {message}"
        self.workflow_logs[execution_id].append(log_entry)
        print(log_entry)


async def get_workflow_orchestrator(task_executor: TaskExecutor) -> WorkflowOrchestrator:
    return WorkflowOrchestrator(task_executor)
