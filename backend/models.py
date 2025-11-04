from sqlalchemy import Column, String, Integer, Text, DateTime, JSON, ForeignKey, Enum as SQLEnum, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from backend.database import Base
import enum
import uuid

def generate_uuid():
    return str(uuid.uuid4())


class WebsiteCredential(Base):
    """Encrypted credentials for website logins"""
    __tablename__ = "website_credentials"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    website_profile_id = Column(String, ForeignKey("website_profiles.id"), nullable=False)
    
    credential_name = Column(String, nullable=False)
    encrypted_username = Column(Text, nullable=False)
    encrypted_password = Column(Text, nullable=False)
    
    login_url = Column(String, nullable=True)
    username_selector = Column(String, nullable=True)
    password_selector = Column(String, nullable=True)
    submit_selector = Column(String, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class TaskStatus(str, enum.Enum):
    ACTIVE = "active"
    DRAFT = "draft"
    DISABLED = "disabled"

class WorkflowStatus(str, enum.Enum):
    ACTIVE = "active"
    DRAFT = "draft"
    DISABLED = "disabled"

class ExecutionStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"

class ProfileStatus(str, enum.Enum):
    LEARNED = "learned"
    LEARNING = "learning"
    OUTDATED = "outdated"
    FAILED = "failed"

class WebsiteProfile(Base):
    __tablename__ = "website_profiles"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    url = Column(String, nullable=False, unique=True, index=True)
    element_count = Column(Integer, default=0)
    version = Column(Integer, default=1)
    status = Column(SQLEnum(ProfileStatus), default=ProfileStatus.LEARNING)
    
    # JSON fields for storing complex data
    dom_map = Column(JSON, nullable=True)  # Complete DOM structure
    interaction_graph = Column(JSON, nullable=True)  # Element relationships
    element_categories = Column(JSON, nullable=True)  # Categorized elements
    selectors = Column(JSON, nullable=True)  # CSS/XPath selectors
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_learned = Column(DateTime(timezone=True))
    
    # Relationships
    tasks = relationship("Task", back_populates="website_profile")

class Task(Base):
    __tablename__ = "tasks"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    title = Column(String, nullable=False)
    description = Column(Text)
    website_profile_id = Column(String, ForeignKey("website_profiles.id"), nullable=False)
    
    status = Column(SQLEnum(TaskStatus), default=TaskStatus.DRAFT)
    
    # AI-generated automation script
    automation_script = Column(JSON, nullable=True)  # Structured automation steps
    parameters = Column(JSON, nullable=True)  # Parametric task variables
    
    run_count = Column(Integer, default=0)
    success_count = Column(Integer, default=0)
    failure_count = Column(Integer, default=0)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_run = Column(DateTime(timezone=True))
    
    # Relationships
    website_profile = relationship("WebsiteProfile", back_populates="tasks")
    executions = relationship("ExecutionHistory", back_populates="task")
    workflow_tasks = relationship("WorkflowTask", back_populates="task")

class Workflow(Base):
    __tablename__ = "workflows"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    title = Column(String, nullable=False)
    description = Column(Text)
    
    status = Column(SQLEnum(WorkflowStatus), default=WorkflowStatus.DRAFT)
    
    # Workflow configuration
    execution_order = Column(JSON, nullable=True)  # Order and dependencies
    data_mapping = Column(JSON, nullable=True)  # Data flow between tasks
    conditional_logic = Column(JSON, nullable=True)  # Branching logic
    
    run_count = Column(Integer, default=0)
    success_count = Column(Integer, default=0)
    failure_count = Column(Integer, default=0)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_run = Column(DateTime(timezone=True))
    
    # Relationships
    workflow_tasks = relationship("WorkflowTask", back_populates="workflow")
    executions = relationship("ExecutionHistory", back_populates="workflow")

class WorkflowTask(Base):
    """Junction table for Workflow-Task many-to-many relationship"""
    __tablename__ = "workflow_tasks"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    workflow_id = Column(String, ForeignKey("workflows.id"), nullable=False)
    task_id = Column(String, ForeignKey("tasks.id"), nullable=False)
    
    order = Column(Integer, nullable=False)  # Execution order within workflow
    is_parallel = Column(Boolean, default=False)  # Can run in parallel with others
    
    # Relationships
    workflow = relationship("Workflow", back_populates="workflow_tasks")
    task = relationship("Task", back_populates="workflow_tasks")

class ExecutionHistory(Base):
    __tablename__ = "execution_history"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    task_id = Column(String, ForeignKey("tasks.id"), nullable=True)
    workflow_id = Column(String, ForeignKey("workflows.id"), nullable=True)
    
    status = Column(SQLEnum(ExecutionStatus), default=ExecutionStatus.PENDING)
    
    # Execution details
    logs = Column(JSON, nullable=True)  # Execution logs
    screenshots = Column(JSON, nullable=True)  # Paths to screenshots
    extracted_data = Column(JSON, nullable=True)  # Data extracted during execution
    error_message = Column(Text, nullable=True)
    
    # AI model used
    model_used = Column(String, nullable=True)  # Which LLM was used
    
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    duration_seconds = Column(Integer)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    task = relationship("Task", back_populates="executions")
    workflow = relationship("Workflow", back_populates="executions")
