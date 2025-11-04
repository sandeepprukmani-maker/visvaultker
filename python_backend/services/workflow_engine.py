import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime
from .task_manager import TaskManager
import json

class WorkflowEngine:
    def __init__(self):
        self.task_manager = TaskManager()
    
    async def execute_workflow(
        self,
        workflow: Dict[str, Any],
        workflow_tasks: List[Dict[str, Any]],
        tasks: Dict[str, Dict[str, Any]],
        initial_parameters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        execution_log = []
        screenshots = []
        data_context = initial_parameters or {}
        
        sorted_workflow_tasks = sorted(workflow_tasks, key=lambda x: x.get("order", 0))
        
        for wf_task in sorted_workflow_tasks:
            task_id = wf_task["taskId"]
            task = tasks.get(task_id)
            
            if not task:
                execution_log.append({
                    "workflow_task_id": wf_task["id"],
                    "error": f"Task {task_id} not found",
                    "status": "failed"
                })
                continue
            
            should_execute = await self._evaluate_condition(
                wf_task.get("condition"),
                data_context
            )
            
            if not should_execute:
                execution_log.append({
                    "workflow_task_id": wf_task["id"],
                    "task_id": task_id,
                    "task_name": task["name"],
                    "status": "skipped",
                    "reason": "condition not met"
                })
                continue
            
            task_parameters = self._merge_parameters(
                wf_task.get("parameters", {}),
                data_context
            )
            
            try:
                result = await self.task_manager.execute_task(task, task_parameters)
                
                execution_log.append({
                    "workflow_task_id": wf_task["id"],
                    "task_id": task_id,
                    "task_name": task["name"],
                    "status": "completed" if result["success"] else "failed",
                    "result": result
                })
                
                if result.get("screenshots"):
                    screenshots.extend(result["screenshots"])
                
                output_data = self._extract_output_data(result)
                data_context.update(output_data)
                
                if not result["success"]:
                    if not workflow.get("continueOnError", False):
                        return {
                            "success": False,
                            "error": f"Task {task['name']} failed",
                            "execution_log": execution_log,
                            "screenshots": screenshots,
                            "data_context": data_context
                        }
            
            except Exception as e:
                execution_log.append({
                    "workflow_task_id": wf_task["id"],
                    "task_id": task_id,
                    "task_name": task["name"],
                    "status": "error",
                    "error": str(e)
                })
                
                if not workflow.get("continueOnError", False):
                    return {
                        "success": False,
                        "error": str(e),
                        "execution_log": execution_log,
                        "screenshots": screenshots,
                        "data_context": data_context
                    }
        
        return {
            "success": True,
            "execution_log": execution_log,
            "screenshots": screenshots,
            "data_context": data_context
        }
    
    async def _evaluate_condition(
        self,
        condition: Optional[str],
        data_context: Dict[str, Any]
    ) -> bool:
        if not condition:
            return True
        
        try:
            safe_globals = {
                "__builtins__": {
                    "len": len,
                    "str": str,
                    "int": int,
                    "float": float,
                    "bool": bool
                }
            }
            
            result = eval(condition, safe_globals, data_context)
            return bool(result)
        except Exception:
            return True
    
    def _merge_parameters(
        self,
        task_parameters: Dict[str, Any],
        data_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        merged = {}
        
        for key, value in task_parameters.items():
            if isinstance(value, str) and value.startswith("$"):
                context_key = value[1:]
                merged[key] = data_context.get(context_key, value)
            else:
                merged[key] = value
        
        return merged
    
    def _extract_output_data(self, result: Dict[str, Any]) -> Dict[str, Any]:
        output = {}
        
        if result.get("result"):
            output["last_result"] = result["result"]
        
        if result.get("execution_log"):
            last_log = result["execution_log"][-1] if result["execution_log"] else {}
            output["last_step_result"] = last_log.get("result")
        
        return output
    
    async def validate_workflow(
        self,
        workflow: Dict[str, Any],
        workflow_tasks: List[Dict[str, Any]],
        tasks: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        issues = []
        
        if not workflow.get("name"):
            issues.append("Workflow must have a name")
        
        if not workflow_tasks:
            issues.append("Workflow must have at least one task")
        
        task_ids = set()
        for wf_task in workflow_tasks:
            task_id = wf_task.get("taskId")
            
            if not task_id:
                issues.append(f"Workflow task missing taskId")
                continue
            
            if task_id in task_ids:
                issues.append(f"Duplicate task {task_id} in workflow")
            task_ids.add(task_id)
            
            if task_id not in tasks:
                issues.append(f"Task {task_id} not found")
            
            if wf_task.get("condition"):
                try:
                    compile(wf_task["condition"], '<string>', 'eval')
                except SyntaxError:
                    issues.append(f"Invalid condition syntax in task {task_id}")
        
        return {
            "valid": len(issues) == 0,
            "issues": issues
        }
    
    async def execute_parallel_tasks(
        self,
        tasks_data: List[tuple[Dict[str, Any], Dict[str, Any]]]
    ) -> List[Dict[str, Any]]:
        async def execute_single(task_and_params):
            task, params = task_and_params
            return await self.task_manager.execute_task(task, params)
        
        results = await asyncio.gather(
            *[execute_single(td) for td in tasks_data],
            return_exceptions=True
        )
        
        return [
            r if not isinstance(r, Exception) else {"success": False, "error": str(r)}
            for r in results
        ]
