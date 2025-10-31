# Jira Acceptance Criteria Automation

## Overview
A Python Flask web application that automates the generation and management of acceptance criteria for Jira EPICs and user stories using AI. The application integrates with Jira's API and provides both manual editing and AI-powered chat-based refinement capabilities.

## Recent Changes
- **Oct 31, 2025 - Refactored OAuth Implementation**: Restructured OAuth code to match enterprise patterns
  - Added modular helper functions: `_ensure_env_vars_for_oauth()`, `_get_token_fetcher()`, `get_access_token()`, `create_client()`
  - Implemented cached token fetcher with automatic refresh
  - Added `send_chat_request()` for flexible message-based requests
  - Uses `GW_BASE_URL` for Gen AI Gateway integration
  - SSL certificate handling with certifi
- **Oct 31, 2025 - Upgraded to JIRA Python Library**: Switched from REST API to official JIRA Python library
  - Installed `jira` package for more reliable Jira integration
  - Rewrote JiraService to use JIRA library with proper authentication
  - Added connection testing and validation on initialization
  - Improved handling of Atlassian Document Format (ADF) descriptions
  - Better error handling and logging for Jira operations
- **Oct 31, 2025 - Removed Mock Data**: Removed mock Jira service, now uses only real Jira API integration
  - Deleted mock_jira_service.py
  - Updated all endpoints to require Jira credentials
  - Added credential validation before Jira API calls
  - Application now requires proper Jira configuration to function
- **Oct 30, 2025 - GitHub Import Setup**: Successfully imported and configured for Replit environment
  - Installed all Python dependencies (Flask, SQLAlchemy, OpenAI, etc.)
  - Configured SQLite fallback for development (switches to PostgreSQL when DATABASE_URL is set)
  - Added postgres:// to postgresql:// URL conversion for Replit PostgreSQL compatibility
  - Set up Flask development workflow on port 5000 with webview
  - Configured production deployment with Gunicorn for autoscale
- **Oct 30, 2025 - Critical Bug Fixes**: Fixed JavaScript injection vulnerability in accept flow, fixed coverage analysis story matching with Jira IDs, fixed redundant story display
- **Oct 30, 2025 - All Scenarios Complete**: Implemented and tested all 10 specification scenarios
- **Oct 30, 2025 - UI Redesign**: Modern GitHub-style dark theme (#0d1117 background, blue accents)
- **Oct 30, 2025 - Initial Setup**: Created full-stack Flask application with PostgreSQL database
- **Database Models**: User, Epic, Story, GeneratedAC, AuditLog
- **Services**: Real Jira API service, OpenAI AI service
- **Frontend**: Bootstrap-based dashboard with coverage analysis and alignment checking
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
  - `jira_service.py`: Jira Python library integration
  - `ai_service.py`: OpenAI integration for AC generation with OAuth support
  - `oauth_config.py`: OAuth configuration and token fetcher classes
  - `openai_oauth.py`: OpenAI OAuth helper functions for Gen AI Gateway

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

### Jira Settings
Configure via Settings page in the UI:
- **Jira URL**: Your Jira instance URL (e.g., https://your-domain.atlassian.net)
- **Username**: Your Jira email
- **Password**: Your Jira API token or password

### OpenAI API Configuration
Two authentication methods supported:

**Option 1: Simple API Key**
```bash
OPENAI_API_KEY=your_openai_api_key
```

**Option 2: OAuth with Gen AI Gateway** (Recommended for Enterprise)
```bash
USE_OAUTH_FOR_OPENAI=true
OAUTH_TOKEN_URL=<your_token_endpoint>
OAUTH_CLIENT_ID=<your_client_id>
OAUTH_CLIENT_SECRET=<your_client_secret>
OAUTH_GRANT_TYPE=client_credentials
OAUTH_SCOPE=<your_scope>
GW_BASE_URL=<your_gateway_base_url>
```

### Database
- PostgreSQL (automatically configured via Replit)

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
