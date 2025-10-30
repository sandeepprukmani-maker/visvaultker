# Jira Acceptance Criteria Automation

## Overview
A Python Flask web application that automates the generation and management of acceptance criteria for Jira EPICs and user stories using AI. The application integrates with Jira's API and provides both manual editing and AI-powered chat-based refinement capabilities.

## Recent Changes
- **Initial Setup (Oct 30, 2025)**: Created full-stack Flask application with PostgreSQL database
- **Database Models**: User, Epic, Story, GeneratedAC, AuditLog
- **Services**: Jira API integration, OpenAI AI service
- **Frontend**: Bootstrap-based dashboard with dual editing modes
- **Authentication**: Replit Auth integration

## Features
1. **EPIC Fetching**: Connect to Jira and fetch EPICs with their user stories
2. **AI Generation**: Automatically generate acceptance criteria from EPIC descriptions
3. **Dual Editing Modes**:
   - Manual inline editor for direct text editing
   - AI chat interface for conversational refinement
4. **Selective Updates**: Choose which stories to update (partial updates)
5. **Single & Bulk Upload**: Update one story or multiple stories at once
6. **Preview/Diff View**: See before/after comparison before pushing to Jira
7. **Settings Management**: Store Jira credentials securely
8. **Audit Logging**: Track all updates with timestamps

## Project Architecture

### Backend (Python/Flask)
- **app.py**: Main Flask application with API routes
- **models.py**: SQLAlchemy database models
- **database.py**: Database configuration
- **services/**:
  - `jira_service.py`: Jira REST API integration
  - `ai_service.py`: OpenAI integration for AC generation

### Frontend
- **templates/**: HTML templates (base, login, dashboard)
- **static/css/style.css**: Custom styling
- **static/js/app.js**: Frontend JavaScript logic

### Database Schema
- `users`: User authentication and Jira credentials
- `epics`: Cached EPIC data from Jira
- `stories`: User stories linked to EPICs
- `generated_acs`: AI-generated acceptance criteria
- `audit_logs`: Change history and audit trail

## Configuration
- **Jira Settings**: Configured via Settings page (URL, username, password)
- **OpenAI API**: Optional - set OPENAI_API_KEY environment variable for AI features
- **Database**: PostgreSQL (automatically configured via Replit)

## User Preferences
- Workflow: Flask development server on port 5000
- Stack: Python 3.11, Flask, PostgreSQL, Bootstrap 5

## 10 Supported Scenarios
1. EPIC with description but no stories → Generate and display AC
2. EPIC with no description → Show error message
3. Update existing stories → Replace ACs with new AI output
4. Add and update stories → Update existing + create new
5. Update single story → Edit and upload one story's AC
6. Upload single story → Push one update to Jira
7. Bulk upload → Push multiple updates at once
8. Manual editing → Edit AC inline before upload
9. Partial updates → Select specific stories with checkboxes
10. Error handling → Clear messages for invalid inputs

## Usage
1. Sign in with Replit Auth
2. Configure Jira credentials in Settings
3. Enter EPIC ID and fetch
4. Generate ACs with AI
5. Edit manually or use AI chat refinement
6. Select stories to update
7. Push to Jira (single or bulk)
