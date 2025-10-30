from database import db
from datetime import datetime

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    name = db.Column(db.String(255))
    password_hash = db.Column(db.String(256))
    replit_user_id = db.Column(db.String(255), unique=True)
    
    jira_url = db.Column(db.String(500))
    jira_username = db.Column(db.String(255))
    jira_password = db.Column(db.String(500))
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    epics = db.relationship('Epic', backref='user', lazy=True, cascade='all, delete-orphan')
    audit_logs = db.relationship('AuditLog', backref='user', lazy=True)

class Epic(db.Model):
    __tablename__ = 'epics'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    jira_epic_id = db.Column(db.String(100), nullable=False)
    title = db.Column(db.String(500), nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    stories = db.relationship('Story', backref='epic', lazy=True, cascade='all, delete-orphan')
    generated_acs = db.relationship('GeneratedAC', backref='epic', lazy=True, cascade='all, delete-orphan')

class Story(db.Model):
    __tablename__ = 'stories'
    
    id = db.Column(db.Integer, primary_key=True)
    epic_id = db.Column(db.Integer, db.ForeignKey('epics.id'), nullable=False)
    jira_story_id = db.Column(db.String(100), nullable=False)
    title = db.Column(db.String(500), nullable=False)
    description = db.Column(db.Text)
    current_ac = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    audit_logs = db.relationship('AuditLog', backref='story', lazy=True)

class GeneratedAC(db.Model):
    __tablename__ = 'generated_acs'
    
    id = db.Column(db.Integer, primary_key=True)
    epic_id = db.Column(db.Integer, db.ForeignKey('epics.id'), nullable=False)
    story_id = db.Column(db.Integer, db.ForeignKey('stories.id'), nullable=True)
    story_title = db.Column(db.String(500))
    ac_text = db.Column(db.Text, nullable=False)
    format = db.Column(db.String(50), default='gherkin')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class AuditLog(db.Model):
    __tablename__ = 'audit_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    epic_id = db.Column(db.Integer, db.ForeignKey('epics.id'), nullable=True)
    story_id = db.Column(db.Integer, db.ForeignKey('stories.id'), nullable=True)
    before_text = db.Column(db.Text)
    after_text = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
