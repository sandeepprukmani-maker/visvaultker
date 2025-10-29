"""
Database Models for AI Browser Automation
"""
import json
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base)


class ExecutionHistory(db.Model):
    """Model for storing automation execution history"""
    
    __tablename__ = 'execution_history'
    
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)
    
    prompt = db.Column(db.Text, nullable=False)
    engine = db.Column(db.String(50), nullable=False)
    headless = db.Column(db.Boolean, nullable=False, default=False)
    
    success = db.Column(db.Boolean, nullable=False, default=False)
    error_message = db.Column(db.Text, nullable=True)
    
    screenshot_path = db.Column(db.Text, nullable=True)  # JSON array of screenshot paths
    execution_logs = db.Column(db.Text, nullable=True)
    
    iterations = db.Column(db.Integer, nullable=True)
    execution_time = db.Column(db.Float, nullable=True)
    
    def to_dict(self):
        """Convert model to dictionary"""
        screenshots = []
        if self.screenshot_path:
            try:
                screenshots = json.loads(self.screenshot_path)
            except (json.JSONDecodeError, TypeError):
                screenshots = [self.screenshot_path] if self.screenshot_path else []
        
        return {
            'id': self.id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'prompt': self.prompt,
            'engine': self.engine,
            'headless': self.headless,
            'success': self.success,
            'error_message': self.error_message,
            'screenshot_path': self.screenshot_path,
            'screenshots': screenshots,
            'execution_logs': self.execution_logs,
            'iterations': self.iterations,
            'execution_time': self.execution_time
        }
