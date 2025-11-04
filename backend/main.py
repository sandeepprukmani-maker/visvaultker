"""
FastAPI Backend for AI Browser Automation Platform
"""

from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime

from backend.database import get_db, init_db
from backend.models import (
    WebsiteProfile, Task, Workflow, ExecutionHistory, WorkflowTask, 
    WebsiteCredential, ProfileStatus, ExecutionStatus
)
from backend.schemas import (
    WebsiteProfileCreate, WebsiteProfileResponse,
    TaskCreate, TaskUpdate, TaskResponse,
    WorkflowCreate, WorkflowUpdate, WorkflowResponse,
    ExecutionRequest, ExecutionResponse,
    LLMModelInfo
)
from backend.llm_manager import llm_manager
from backend.browser_engine import browser_engine
from backend.website_explorer import WebsiteExplorer
from backend.task_executor import TaskExecutor
from backend.workflow_orchestrator import WorkflowOrchestrator
from backend.credential_manager import credential_manager
from pydantic import BaseModel

app = FastAPI(title="AutomateAI Backend")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global instances
explorer: Optional[WebsiteExplorer] = None
task_executor: Optional[TaskExecutor] = None
workflow_orchestrator: Optional[WorkflowOrchestrator] = None

# Initialize database and browser on startup
@app.on_event("startup")
async def startup_event():
    global explorer, task_executor, workflow_orchestrator
    init_db()
    await browser_engine.initialize()
    explorer = WebsiteExplorer(browser_engine)
    task_executor = TaskExecutor(browser_engine)
    workflow_orchestrator = WorkflowOrchestrator(task_executor)

@app.on_event("shutdown")
async def shutdown_event():
    await browser_engine.close()

# Health check
@app.get("/api/health")
async def health_check():
    return {"status": "healthy"}

# Website Profile Endpoints
@app.get("/api/profiles", response_model=List[WebsiteProfileResponse])
async def list_profiles(db: Session = Depends(get_db)):
    """List all learned website profiles"""
    profiles = db.query(WebsiteProfile).all()
    return profiles

@app.post("/api/profiles", response_model=WebsiteProfileResponse)
async def create_profile(
    profile: WebsiteProfileCreate, 
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Start learning a new website"""
    existing = db.query(WebsiteProfile).filter(WebsiteProfile.url == profile.url).first()
    if existing:
        raise HTTPException(status_code=400, detail="Website profile already exists")
    
    new_profile = WebsiteProfile(url=profile.url, status=ProfileStatus.LEARNING)
    db.add(new_profile)
    db.commit()
    db.refresh(new_profile)
    
    # Trigger async website learning - pass profile_id only, not the session
    background_tasks.add_task(learn_website_task, new_profile.id, profile.url)
    
    return new_profile

@app.get("/api/profiles/{profile_id}", response_model=WebsiteProfileResponse)
async def get_profile(profile_id: str, db: Session = Depends(get_db)):
    """Get a specific website profile"""
    profile = db.query(WebsiteProfile).filter(WebsiteProfile.id == profile_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile

# Task Endpoints
@app.get("/api/tasks", response_model=List[TaskResponse])
async def list_tasks(db: Session = Depends(get_db)):
    """List all tasks"""
    tasks = db.query(Task).all()
    return tasks

@app.post("/api/tasks", response_model=TaskResponse)
async def create_task(task: TaskCreate, db: Session = Depends(get_db)):
    """Create a new automation task"""
    # Verify website profile exists
    profile = db.query(WebsiteProfile).filter(WebsiteProfile.id == task.website_profile_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Website profile not found")
    
    new_task = Task(
        title=task.title,
        description=task.description,
        website_profile_id=task.website_profile_id
    )
    db.add(new_task)
    db.commit()
    db.refresh(new_task)
    
    # TODO: Use LLM to generate automation script
    
    return new_task

@app.get("/api/tasks/{task_id}", response_model=TaskResponse)
async def get_task(task_id: str, db: Session = Depends(get_db)):
    """Get a specific task"""
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@app.patch("/api/tasks/{task_id}", response_model=TaskResponse)
async def update_task(task_id: str, task_update: TaskUpdate, db: Session = Depends(get_db)):
    """Update a task"""
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    update_data = task_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(task, field, value)
    
    db.commit()
    db.refresh(task)
    return task

@app.delete("/api/tasks/{task_id}")
async def delete_task(task_id: str, db: Session = Depends(get_db)):
    """Delete a task"""
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    db.delete(task)
    db.commit()
    return {"message": "Task deleted successfully"}

# Workflow Endpoints
@app.get("/api/workflows", response_model=List[WorkflowResponse])
async def list_workflows(db: Session = Depends(get_db)):
    """List all workflows"""
    workflows = db.query(Workflow).all()
    return workflows

@app.post("/api/workflows", response_model=WorkflowResponse)
async def create_workflow(workflow: WorkflowCreate, db: Session = Depends(get_db)):
    """Create a new workflow"""
    new_workflow = Workflow(
        title=workflow.title,
        description=workflow.description
    )
    db.add(new_workflow)
    db.flush()  # Get the ID before adding workflow_tasks
    
    # Add tasks to workflow
    for order, task_id in enumerate(workflow.task_ids):
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
        
        workflow_task = WorkflowTask(
            workflow_id=new_workflow.id,
            task_id=task_id,
            order=order
        )
        db.add(workflow_task)
    
    db.commit()
    db.refresh(new_workflow)
    return new_workflow

@app.get("/api/workflows/{workflow_id}", response_model=WorkflowResponse)
async def get_workflow(workflow_id: str, db: Session = Depends(get_db)):
    """Get a specific workflow"""
    workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return workflow

# Execution Endpoints
@app.post("/api/execute", response_model=ExecutionResponse)
async def execute_automation(
    execution: ExecutionRequest, 
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Execute a task or workflow"""
    if not execution.task_id and not execution.workflow_id:
        raise HTTPException(status_code=400, detail="Either task_id or workflow_id must be provided")
    
    if execution.task_id:
        task = db.query(Task).filter(Task.id == execution.task_id).first()
        if not task:
            raise HTTPException(status_code=404, detail=f"Task {execution.task_id} not found")
    
    if execution.workflow_id:
        workflow = db.query(Workflow).filter(Workflow.id == execution.workflow_id).first()
        if not workflow:
            raise HTTPException(status_code=404, detail=f"Workflow {execution.workflow_id} not found")
    
    new_execution = ExecutionHistory(
        task_id=execution.task_id,
        workflow_id=execution.workflow_id,
        status=ExecutionStatus.PENDING,
        started_at=datetime.utcnow()
    )
    db.add(new_execution)
    db.commit()
    db.refresh(new_execution)
    
    # Trigger async execution - pass execution_id only, not the session
    background_tasks.add_task(
        execute_automation_task,
        new_execution.id,
        execution.task_id,
        execution.workflow_id,
        execution.parameters
    )
    
    return new_execution

@app.get("/api/executions/{execution_id}", response_model=ExecutionResponse)
async def get_execution(execution_id: str, db: Session = Depends(get_db)):
    """Get execution status and results"""
    execution = db.query(ExecutionHistory).filter(ExecutionHistory.id == execution_id).first()
    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")
    return execution

# LLM Configuration Endpoints
@app.get("/api/llm/models", response_model=List[LLMModelInfo])
async def list_llm_models():
    """List available LLM models"""
    models = llm_manager.list_models()
    return [
        LLMModelInfo(
            id=m['id'],
            name=m.get('model_name', m['id']),
            provider=m['provider'],
            capabilities=m['capabilities'],
            cost_tier=m['cost_tier'],
            enabled=m['enabled']
        )
        for m in models
    ]

@app.get("/api/llm/models/{model_id}")
async def get_llm_model(model_id: str):
    """Get information about a specific LLM model"""
    info = llm_manager.get_model_info(model_id)
    if not info:
        raise HTTPException(status_code=404, detail="Model not found")
    return {"id": model_id, **info}

# Credential Management Endpoints
class CredentialCreate(BaseModel):
    credential_name: str
    username: str
    password: str
    login_url: Optional[str] = None
    username_selector: Optional[str] = None
    password_selector: Optional[str] = None
    submit_selector: Optional[str] = None

@app.post("/api/profiles/{profile_id}/credentials")
async def store_credentials(
    profile_id: str,
    credential: CredentialCreate,
    db: Session = Depends(get_db)
):
    """Store encrypted credentials for a website profile"""
    profile = db.query(WebsiteProfile).filter(WebsiteProfile.id == profile_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    selectors = {
        'username': credential.username_selector,
        'password': credential.password_selector,
        'submit': credential.submit_selector
    }
    
    credential_data = credential_manager.store_credentials(
        profile_id,
        credential.credential_name,
        credential.username,
        credential.password,
        credential.login_url,
        selectors
    )
    
    new_credential = WebsiteCredential(**credential_data)
    db.add(new_credential)
    db.commit()
    
    return {"message": "Credentials stored successfully", "id": credential_data['id']}

@app.get("/api/profiles/{profile_id}/credentials")
async def list_credentials(profile_id: str, db: Session = Depends(get_db)):
    """List credentials for a profile (without sensitive data)"""
    credentials = db.query(WebsiteCredential).filter(
        WebsiteCredential.website_profile_id == profile_id
    ).all()
    
    return [{
        'id': c.id,
        'credential_name': c.credential_name,
        'login_url': c.login_url,
        'created_at': c.created_at
    } for c in credentials]

# Background Tasks
async def learn_website_task(profile_id: str, url: str):
    """Background task to learn a website - creates its own DB session"""
    from backend.database import SessionLocal
    
    db = SessionLocal()
    try:
        result = await explorer.explore_website(url, profile_id)
        
        profile = db.query(WebsiteProfile).filter(WebsiteProfile.id == profile_id).first()
        if profile:
            profile.dom_map = result['dom_map']
            profile.interaction_graph = result['interaction_graph']
            profile.element_categories = result['element_categories']
            profile.selectors = result['selectors']
            profile.element_count = result['element_count']
            profile.status = ProfileStatus.LEARNED
            profile.last_learned = datetime.utcnow()
            db.commit()
    except Exception as e:
        print(f"Error learning website {url}: {e}")
        profile = db.query(WebsiteProfile).filter(WebsiteProfile.id == profile_id).first()
        if profile:
            profile.status = ProfileStatus.FAILED
            db.commit()
    finally:
        db.close()

async def execute_automation_task(
    execution_id: str,
    task_id: Optional[str],
    workflow_id: Optional[str],
    parameters: Optional[Dict[str, Any]]
):
    """Background task to execute automation - creates its own DB session"""
    from backend.database import SessionLocal
    
    db = SessionLocal()
    try:
        execution = db.query(ExecutionHistory).filter(ExecutionHistory.id == execution_id).first()
        if not execution:
            return
        
        execution.status = ExecutionStatus.RUNNING
        db.commit()
        
        if task_id:
            # Execute single task
            task = db.query(Task).filter(Task.id == task_id).first()
            profile = db.query(WebsiteProfile).filter(WebsiteProfile.id == task.website_profile_id).first()
            
            # Get credentials if available
            credentials_db = db.query(WebsiteCredential).filter(
                WebsiteCredential.website_profile_id == profile.id
            ).first()
            
            credentials = None
            if credentials_db:
                credentials = credential_manager.retrieve_credentials(
                    credentials_db.id,
                    {
                        'encrypted_username': credentials_db.encrypted_username,
                        'encrypted_password': credentials_db.encrypted_password,
                        'login_url': credentials_db.login_url,
                        'username_selector': credentials_db.username_selector,
                        'password_selector': credentials_db.password_selector,
                        'submit_selector': credentials_db.submit_selector
                    }
                )
            
            result = await task_executor.execute_task(
                task_id,
                {
                    'id': task.id,
                    'title': task.title,
                    'description': task.description,
                    'automation_script': task.automation_script
                },
                {
                    'id': profile.id,
                    'url': profile.url,
                    'selectors': profile.selectors
                },
                parameters=parameters,
                credentials=credentials
            )
            
            execution.status = ExecutionStatus.SUCCESS if result.get('status') == 'success' else ExecutionStatus.FAILED
            execution.logs = result.get('logs')
            execution.screenshots = result.get('screenshots')
            execution.extracted_data = result.get('extracted_data')
            execution.error_message = result.get('error')
            
            # Update task stats
            task.run_count += 1
            if execution.status == ExecutionStatus.SUCCESS:
                task.success_count += 1
            else:
                task.failure_count += 1
            task.last_run = datetime.utcnow()
        
        elif workflow_id:
            # Execute workflow - implementation would be similar
            pass
        
        execution.completed_at = datetime.utcnow()
        if execution.started_at:
            duration = (execution.completed_at - execution.started_at).total_seconds()
            execution.duration_seconds = int(duration)
        
        db.commit()
        
    except Exception as e:
        print(f"Error executing automation: {e}")
        execution = db.query(ExecutionHistory).filter(ExecutionHistory.id == execution_id).first()
        if execution:
            execution.status = ExecutionStatus.FAILED
            execution.error_message = str(e)
            execution.completed_at = datetime.utcnow()
            db.commit()
    finally:
        db.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
