"""
Pydantic schemas for request/response validation
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from backend.models import TaskStatus, WorkflowStatus, ExecutionStatus, ProfileStatus

# Website Profile Schemas
class WebsiteProfileCreate(BaseModel):
    url: str = Field(..., description="Website URL to learn")

class WebsiteProfileResponse(BaseModel):
    id: str
    url: str
    element_count: int
    version: int
    status: ProfileStatus
    last_learned: Optional[datetime] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

# Task Schemas
class TaskCreate(BaseModel):
    title: str
    description: str
    website_profile_id: str

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[TaskStatus] = None

class TaskResponse(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    website_profile_id: str
    status: TaskStatus
    run_count: int
    success_count: int
    failure_count: int
    last_run: Optional[datetime] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

# Workflow Schemas
class WorkflowCreate(BaseModel):
    title: str
    description: str
    task_ids: List[str]  # List of task IDs to include

class WorkflowUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[WorkflowStatus] = None

class WorkflowResponse(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    status: WorkflowStatus
    run_count: int
    success_count: int
    failure_count: int
    last_run: Optional[datetime] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

# Execution Schemas
class ExecutionRequest(BaseModel):
    task_id: Optional[str] = None
    workflow_id: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None

class ExecutionResponse(BaseModel):
    id: str
    task_id: Optional[str] = None
    workflow_id: Optional[str] = None
    status: ExecutionStatus
    model_used: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[int] = None
    error_message: Optional[str] = None
    
    class Config:
        from_attributes = True

# LLM Model Info
class LLMModelInfo(BaseModel):
    id: str
    name: str
    provider: str
    capabilities: List[str]
    cost_tier: str
    enabled: bool
