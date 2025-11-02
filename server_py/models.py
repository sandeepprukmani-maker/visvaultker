from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel, Field
from uuid import uuid4

class CrawlSession(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    url: str
    depth: int = 3
    status: str = "pending"
    pages_found: int = Field(default=0, alias="pagesFound")
    elements_found: int = Field(default=0, alias="elementsFound")
    started_at: datetime = Field(default_factory=datetime.now, alias="startedAt")
    completed_at: Optional[datetime] = Field(default=None, alias="completedAt")

    class Config:
        populate_by_name = True

class InsertCrawlSession(BaseModel):
    url: str
    depth: int = 3
    status: Optional[str] = None

class Page(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    crawl_session_id: str = Field(alias="crawlSessionId")
    url: str
    title: str
    element_count: int = Field(default=0, alias="elementCount")
    screenshot: Optional[str] = None
    template_hash: Optional[str] = Field(default=None, alias="templateHash")
    template_group: Optional[int] = Field(default=None, alias="templateGroup")
    crawled_at: datetime = Field(default_factory=datetime.now, alias="crawledAt")

    class Config:
        populate_by_name = True

class InsertPage(BaseModel):
    crawl_session_id: str = Field(alias="crawlSessionId")
    url: str
    title: str
    element_count: int = Field(default=0, alias="elementCount")
    screenshot: Optional[str] = None
    template_hash: Optional[str] = Field(default=None, alias="templateHash")
    template_group: Optional[int] = Field(default=None, alias="templateGroup")

    class Config:
        populate_by_name = True

class Element(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    page_id: str = Field(alias="pageId")
    tag: str
    selector: str
    text: Optional[str] = None
    attributes: dict[str, Any] = Field(default_factory=dict)
    xpath: Optional[str] = None
    confidence: int = 100
    embedding: Optional[str] = None

    class Config:
        populate_by_name = True

class InsertElement(BaseModel):
    page_id: str = Field(alias="pageId")
    tag: str
    selector: str
    text: Optional[str] = None
    attributes: dict[str, Any] = Field(default_factory=dict)
    xpath: Optional[str] = None
    confidence: int = 100
    embedding: Optional[str] = None

    class Config:
        populate_by_name = True

class Automation(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    command: str
    status: str = "queued"
    plan: Optional[dict[str, Any]] = None
    result: Optional[dict[str, Any]] = None
    duration: Optional[int] = None
    action_count: int = Field(default=0, alias="actionCount")
    created_at: datetime = Field(default_factory=datetime.now, alias="createdAt")
    completed_at: Optional[datetime] = Field(default=None, alias="completedAt")

    class Config:
        populate_by_name = True

class InsertAutomation(BaseModel):
    command: str
    plan: Optional[dict[str, Any]] = None
    result: Optional[dict[str, Any]] = None

    class Config:
        populate_by_name = True

class AutomationLog(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    automation_id: str = Field(alias="automationId")
    timestamp: datetime = Field(default_factory=datetime.now)
    action: str
    status: str
    details: Optional[str] = None
    screenshot: Optional[str] = None

    class Config:
        populate_by_name = True

class InsertAutomationLog(BaseModel):
    automation_id: str = Field(alias="automationId")
    action: str
    status: str
    details: Optional[str] = None
    screenshot: Optional[str] = None

    class Config:
        populate_by_name = True
