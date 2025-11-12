from sqlalchemy import Column, Integer, String, Boolean, Text, DateTime, JSON, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from datetime import datetime
from typing import List, Dict, Optional

Base = declarative_base()

class AutomationHistory(Base):
    __tablename__ = "automation_history"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    prompt = Column(Text, nullable=False)
    prompt_embedding = Column(JSON, nullable=True)
    detected_url = Column(Text, nullable=True)
    mode = Column(String(50), nullable=False)
    model = Column(String(100), nullable=False)
    success = Column(Boolean, nullable=False)
    session_id = Column(String(100), nullable=False)
    logs = Column(JSON, nullable=False)
    generated_code = Column(JSON, nullable=False)
    screenshot = Column(Text, nullable=True)
    error = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, server_default=func.now())
    
    def to_dict(self):
        return {
            "id": self.id,
            "prompt": self.prompt,
            "promptEmbedding": self.prompt_embedding,
            "detectedUrl": self.detected_url,
            "mode": self.mode,
            "model": self.model,
            "success": self.success,
            "sessionId": self.session_id,
            "logs": self.logs,
            "generatedCode": self.generated_code,
            "screenshot": self.screenshot,
            "error": self.error,
            "createdAt": self.created_at.isoformat() if self.created_at is not None else None
        }
