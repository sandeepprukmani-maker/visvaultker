"""
FastAPI Backend for AI Browser Automation Platform
"""

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List

from backend.database import get_db, init_db
from backend.models import WebsiteProfile, Task, Workflow, ExecutionHistory, WorkflowTask
from backend.schemas import (
    WebsiteProfileCreate, WebsiteProfileResponse,
    TaskCreate, TaskUpdate, TaskResponse,
    WorkflowCreate, WorkflowUpdate, WorkflowResponse,
    ExecutionRequest, ExecutionResponse,
    LLMModelInfo
)
from backend.llm_manager import llm_manager

app = FastAPI(title="AutomateAI Backend")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure based on your needs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    init_db()

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
async def create_profile(profile: WebsiteProfileCreate, db: Session = Depends(get_db)):
    """Start learning a new website"""
    # Check if profile already exists
    existing = db.query(WebsiteProfile).filter(WebsiteProfile.url == profile.url).first()
    if existing:
        raise HTTPException(status_code=400, detail="Website profile already exists")
    
    new_profile = WebsiteProfile(url=profile.url)
    db.add(new_profile)
    db.commit()
    db.refresh(new_profile)
    
    # TODO: Trigger async website learning process
    
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
async def execute_automation(execution: ExecutionRequest, db: Session = Depends(get_db)):
    """Execute a task or workflow"""
    if not execution.task_id and not execution.workflow_id:
        raise HTTPException(status_code=400, detail="Either task_id or workflow_id must be provided")
    
    # Validate that referenced task or workflow exists
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
        workflow_id=execution.workflow_id
    )
    db.add(new_execution)
    db.commit()
    db.refresh(new_execution)
    
    # TODO: Trigger async execution
    
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
