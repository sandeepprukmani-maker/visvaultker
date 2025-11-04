from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
import os
import asyncio
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor
import json

from services.llm_manager import LLMManager
from services.browser_automation import BrowserAutomation
from services.website_profiler import WebsiteProfiler
from services.task_manager import TaskManager
from services.workflow_engine import WorkflowEngine

app = FastAPI(title="AutomateAI API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

llm_manager = LLMManager()
task_manager = TaskManager()
workflow_engine = WorkflowEngine()

def get_db():
    return psycopg2.connect(os.getenv("DATABASE_URL"))

class WebsiteProfileRequest(BaseModel):
    url: str

class TaskTeachRequest(BaseModel):
    name: str
    description: str
    websiteUrl: str
    demonstration: List[Dict[str, Any]]
    userId: Optional[str] = None

class TaskExecuteRequest(BaseModel):
    taskId: str
    parameters: Optional[Dict[str, Any]] = None
    userId: Optional[str] = None

class WorkflowCreateRequest(BaseModel):
    name: str
    description: Optional[str] = None
    tasks: List[Dict[str, Any]]
    userId: Optional[str] = None

class WorkflowExecuteRequest(BaseModel):
    workflowId: str
    parameters: Optional[Dict[str, Any]] = None
    userId: Optional[str] = None

@app.get("/")
async def root():
    return {
        "message": "AutomateAI API",
        "version": "1.0.0",
        "endpoints": {
            "tasks": "/api/tasks",
            "workflows": "/api/workflows",
            "profiles": "/api/website-profiles",
            "executions": "/api/executions"
        }
    }

@app.get("/api/tasks")
async def get_tasks(user_id: Optional[str] = None):
    conn = get_db()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            if user_id:
                cur.execute("SELECT * FROM tasks WHERE user_id = %s ORDER BY created_at DESC", (user_id,))
            else:
                cur.execute("SELECT * FROM tasks ORDER BY created_at DESC")
            tasks = cur.fetchall()
            return [dict(task) for task in tasks]
    finally:
        conn.close()

@app.get("/api/tasks/{task_id}")
async def get_task(task_id: str):
    conn = get_db()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM tasks WHERE id = %s", (task_id,))
            task = cur.fetchone()
            if not task:
                raise HTTPException(status_code=404, detail="Task not found")
            return dict(task)
    finally:
        conn.close()

@app.post("/api/tasks/teach")
async def teach_task(request: TaskTeachRequest):
    try:
        task_data = await task_manager.teach_task(
            name=request.name,
            description=request.description,
            website_url=request.websiteUrl,
            demonstration=request.demonstration
        )
        
        conn = get_db()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    INSERT INTO tasks (name, description, category, tags, website_url, steps, parameters, user_id)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING *
                """, (
                    task_data["name"],
                    task_data["description"],
                    task_data["category"],
                    task_data["tags"],
                    task_data["websiteUrl"],
                    json.dumps(task_data["steps"]),
                    json.dumps(task_data["parameters"]),
                    request.userId
                ))
                conn.commit()
                task = cur.fetchone()
                return dict(task)
        finally:
            conn.close()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/tasks/{task_id}/execute")
async def execute_task(task_id: str, request: TaskExecuteRequest, background_tasks: BackgroundTasks):
    conn = get_db()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM tasks WHERE id = %s", (task_id,))
            task = cur.fetchone()
            if not task:
                raise HTTPException(status_code=404, detail="Task not found")
            
            cur.execute("""
                INSERT INTO executions (task_id, status, user_id)
                VALUES (%s, %s, %s)
                RETURNING id
            """, (task_id, "running", request.userId))
            conn.commit()
            execution_id = cur.fetchone()["id"]
        
        background_tasks.add_task(
            run_task_execution,
            execution_id,
            dict(task),
            request.parameters
        )
        
        return {
            "executionId": execution_id,
            "status": "started",
            "taskId": task_id
        }
    finally:
        conn.close()

async def run_task_execution(execution_id: str, task: Dict, parameters: Optional[Dict]):
    conn = get_db()
    try:
        result = await task_manager.execute_task(task, parameters)
        
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE executions
                SET status = %s, completed_at = %s, result = %s, screenshots = %s
                WHERE id = %s
            """, (
                "completed" if result["success"] else "failed",
                datetime.now(),
                json.dumps(result.get("execution_log", [])),
                result.get("screenshots", []),
                execution_id
            ))
            conn.commit()
    except Exception as e:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE executions
                SET status = %s, completed_at = %s, error = %s
                WHERE id = %s
            """, ("error", datetime.now(), str(e), execution_id))
            conn.commit()
    finally:
        conn.close()

@app.get("/api/workflows")
async def get_workflows(user_id: Optional[str] = None):
    conn = get_db()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            if user_id:
                cur.execute("SELECT * FROM workflows WHERE user_id = %s ORDER BY created_at DESC", (user_id,))
            else:
                cur.execute("SELECT * FROM workflows ORDER BY created_at DESC")
            workflows = cur.fetchall()
            return [dict(wf) for wf in workflows]
    finally:
        conn.close()

@app.get("/api/workflows/{workflow_id}")
async def get_workflow(workflow_id: str):
    conn = get_db()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM workflows WHERE id = %s", (workflow_id,))
            workflow = cur.fetchone()
            if not workflow:
                raise HTTPException(status_code=404, detail="Workflow not found")
            
            cur.execute("""
                SELECT wt.*, t.name as task_name
                FROM workflow_tasks wt
                JOIN tasks t ON t.id = wt.task_id
                WHERE wt.workflow_id = %s
                ORDER BY wt.order
            """, (workflow_id,))
            tasks = cur.fetchall()
            
            workflow_dict = dict(workflow)
            workflow_dict["tasks"] = [dict(t) for t in tasks]
            return workflow_dict
    finally:
        conn.close()

@app.post("/api/workflows")
async def create_workflow(request: WorkflowCreateRequest):
    conn = get_db()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                INSERT INTO workflows (name, description, user_id)
                VALUES (%s, %s, %s)
                RETURNING *
            """, (request.name, request.description, request.userId))
            workflow = cur.fetchone()
            workflow_id = workflow["id"]
            
            for order, task in enumerate(request.tasks):
                cur.execute("""
                    INSERT INTO workflow_tasks (workflow_id, task_id, "order", condition, parameters)
                    VALUES (%s, %s, %s, %s, %s)
                """, (
                    workflow_id,
                    task["taskId"],
                    order,
                    task.get("condition"),
                    json.dumps(task.get("parameters", {}))
                ))
            
            conn.commit()
            return dict(workflow)
    finally:
        conn.close()

@app.post("/api/workflows/{workflow_id}/execute")
async def execute_workflow(workflow_id: str, request: WorkflowExecuteRequest, background_tasks: BackgroundTasks):
    conn = get_db()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM workflows WHERE id = %s", (workflow_id,))
            workflow = cur.fetchone()
            if not workflow:
                raise HTTPException(status_code=404, detail="Workflow not found")
            
            cur.execute("""
                INSERT INTO executions (workflow_id, status, user_id)
                VALUES (%s, %s, %s)
                RETURNING id
            """, (workflow_id, "running", request.userId))
            conn.commit()
            execution_id = cur.fetchone()["id"]
        
        background_tasks.add_task(
            run_workflow_execution,
            execution_id,
            workflow_id
        )
        
        return {
            "executionId": execution_id,
            "status": "started",
            "workflowId": workflow_id
        }
    finally:
        conn.close()

async def run_workflow_execution(execution_id: str, workflow_id: str):
    conn = get_db()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM workflows WHERE id = %s", (workflow_id,))
            workflow = dict(cur.fetchone())
            
            cur.execute("""
                SELECT * FROM workflow_tasks WHERE workflow_id = %s ORDER BY "order"
            """, (workflow_id,))
            workflow_tasks = [dict(wt) for wt in cur.fetchall()]
            
            task_ids = [wt["task_id"] for wt in workflow_tasks]
            cur.execute("SELECT * FROM tasks WHERE id = ANY(%s)", (task_ids,))
            tasks = {str(t["id"]): dict(t) for t in cur.fetchall()}
        
        result = await workflow_engine.execute_workflow(
            workflow,
            workflow_tasks,
            tasks,
            {}
        )
        
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE executions
                SET status = %s, completed_at = %s, result = %s, screenshots = %s
                WHERE id = %s
            """, (
                "completed" if result["success"] else "failed",
                datetime.now(),
                json.dumps(result.get("execution_log", [])),
                result.get("screenshots", []),
                execution_id
            ))
            conn.commit()
    except Exception as e:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE executions
                SET status = %s, completed_at = %s, error = %s
                WHERE id = %s
            """, ("error", datetime.now(), str(e), execution_id))
            conn.commit()
    finally:
        conn.close()

@app.post("/api/website-profiles")
async def create_website_profile(request: WebsiteProfileRequest):
    try:
        profiler = WebsiteProfiler()
        profile = await profiler.profile_website(request.url)
        
        conn = get_db()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    INSERT INTO website_profiles (url, name, dom_structure, interaction_graph, element_map, screenshots)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (url) DO UPDATE
                    SET dom_structure = EXCLUDED.dom_structure,
                        interaction_graph = EXCLUDED.interaction_graph,
                        element_map = EXCLUDED.element_map,
                        screenshots = EXCLUDED.screenshots,
                        last_explored = NOW(),
                        version = website_profiles.version + 1
                    RETURNING *
                """, (
                    profile["url"],
                    profile["name"],
                    json.dumps(profile["domStructure"]),
                    json.dumps(profile["interactionGraph"]),
                    json.dumps(profile["elementMap"]),
                    profile["screenshots"]
                ))
                conn.commit()
                result = cur.fetchone()
                return dict(result)
        finally:
            conn.close()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/website-profiles")
async def get_website_profiles():
    conn = get_db()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM website_profiles ORDER BY last_explored DESC")
            profiles = cur.fetchall()
            return [dict(p) for p in profiles]
    finally:
        conn.close()

@app.get("/api/executions")
async def get_executions(user_id: Optional[str] = None, limit: int = 50):
    conn = get_db()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            if user_id:
                cur.execute("""
                    SELECT e.*, t.name as task_name, w.name as workflow_name
                    FROM executions e
                    LEFT JOIN tasks t ON t.id = e.task_id
                    LEFT JOIN workflows w ON w.id = e.workflow_id
                    WHERE e.user_id = %s
                    ORDER BY e.started_at DESC
                    LIMIT %s
                """, (user_id, limit))
            else:
                cur.execute("""
                    SELECT e.*, t.name as task_name, w.name as workflow_name
                    FROM executions e
                    LEFT JOIN tasks t ON t.id = e.task_id
                    LEFT JOIN workflows w ON w.id = e.workflow_id
                    ORDER BY e.started_at DESC
                    LIMIT %s
                """, (limit,))
            executions = cur.fetchall()
            return [dict(e) for e in executions]
    finally:
        conn.close()

@app.get("/api/analytics/overview")
async def get_analytics_overview():
    conn = get_db()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT COUNT(*) as total FROM tasks")
            total_tasks = cur.fetchone()["total"]
            
            cur.execute("SELECT COUNT(*) as total FROM workflows")
            total_workflows = cur.fetchone()["total"]
            
            cur.execute("SELECT COUNT(*) as total FROM executions WHERE DATE(started_at) = CURRENT_DATE")
            executions_today = cur.fetchone()["total"]
            
            cur.execute("SELECT COUNT(*) as total FROM website_profiles")
            websites_learned = cur.fetchone()["total"]
            
            cur.execute("""
                SELECT COUNT(*) as active FROM tasks
                WHERE id IN (
                    SELECT DISTINCT task_id FROM executions
                    WHERE started_at > NOW() - INTERVAL '7 days'
                )
            """)
            active_tasks = cur.fetchone()["active"]
            
            return {
                "totalTasks": total_tasks,
                "activeTasks": active_tasks,
                "totalWorkflows": total_workflows,
                "executionsToday": executions_today,
                "websitesLearned": websites_learned
            }
    finally:
        conn.close()

@app.get("/api/analytics/llm-usage")
async def get_llm_usage():
    usage_stats = llm_manager.get_usage_stats()
    total_cost = llm_manager.get_total_cost()
    
    by_provider = {}
    for stat in usage_stats:
        provider = stat["provider"]
        if provider not in by_provider:
            by_provider[provider] = {
                "calls": 0,
                "total_tokens": 0,
                "total_cost": 0
            }
        by_provider[provider]["calls"] += 1
        by_provider[provider]["total_tokens"] += stat["prompt_tokens"] + stat["completion_tokens"]
        by_provider[provider]["total_cost"] += stat["total_cost"]
    
    return {
        "total_cost": total_cost,
        "by_provider": by_provider,
        "recent_calls": usage_stats[-10:]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
