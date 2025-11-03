# AI Browser Automation - VisionVault

## Overview
VisionVault is an AI-powered browser automation platform that enables users to create browser automations using natural language. The application uses AI models to interpret user requests and execute browser actions using Playwright.

**Current State**: The application is fully functional and running on Replit. The web interface is accessible and ready for use.

## Technology Stack
- **Backend**: Python 3.11 with Flask
- **Frontend**: HTML/CSS/JavaScript (vanilla)
- **Database**: SQLite
- **Browser Automation**: Playwright with dual engine support
  - Browser Use (optimized browser automation)
  - Playwright MCP (Model Context Protocol integration)
- **Node.js Integration**: Playwright MCP server (Node.js 20)

## Project Architecture

### Key Components
1. **Flask Application** (`app/__init__.py`)
   - Handles routing and API endpoints
   - Manages database connections
   - Configures CORS and security middleware
   - Implements cache control for better user experience

2. **Automation Engines** (`app/engines/`)
   - **Browser Use Engine**: Optimized for browser automation tasks
   - **Playwright MCP**: Advanced automation with Model Context Protocol

3. **Services** (`app/services/`)
   - **Engine Orchestrator**: Routes automation tasks to appropriate engines
   - **Intelligent Validator**: Validates and enhances user prompts
   - **Locator Extractor**: Extracts UI element locators

4. **Frontend** (`app/templates/` and `app/static/`)
   - Dashboard for creating automations
   - Configuration page for browser settings
   - Credentials management (encrypted storage)
   - History tracking

### Database
- SQLite database (`automation_history.db`)
- Stores automation history, configurations, and encrypted credentials

### Privacy & Security
- All external telemetry disabled by default
- No cloud sync - data stays local
- Optional credential vault with Fernet encryption
- Optional API key authentication for API endpoints

## Environment Configuration

### Required Environment Variables (Optional)
The application runs without these but AI features require OAuth configuration:

```bash
# OAuth Configuration (for AI features)
OAUTH_TOKEN_URL=
OAUTH_CLIENT_ID=
OAUTH_CLIENT_SECRET=
OAUTH_GRANT_TYPE=
OAUTH_SCOPE=
GW_BASE_URL=

# API Security (optional)
API_KEY=

# Credential Vault (optional)
ENCRYPTION_KEY=
```

### Auto-configured Settings
These are automatically set for optimal operation:
- `ANONYMIZED_TELEMETRY=false`
- `BROWSER_USE_CLOUD_SYNC=false`
- `PLAYWRIGHT_SKIP_VALIDATE_HOST_REQUIREMENTS=1`
- `SESSION_SECRET` (auto-generated if not provided)

## Running the Application

### Development
The application is configured to run on port 5000 with the workflow:
```bash
python main.py
```

The Flask server binds to `0.0.0.0:5000` for Replit compatibility.

### Deployment
For production deployment, use the deployment configuration with gunicorn:
```bash
gunicorn --bind=0.0.0.0:5000 --reuse-port main:app
```

## Configuration Files

### `config/config.ini`
Central configuration file for:
- Browser settings (headless mode, browser type)
- AI model configuration
- Logging levels and detail
- Performance tuning (wait times, retry settings)
- Advanced features (screenshots, PDFs, cookies)
- MCP server mode

### Key Settings
- **Browser Performance**: Optimized for fast execution (50-70% faster than defaults)
- **Max Steps**: 60 steps for complex automation tasks
- **Server Mode**: `always_run` - keeps MCP server running for faster response

## Features

### Core Functionality
1. **Natural Language Automation**: Describe tasks in plain English
2. **Dual Engine Support**: Choose between Browser Use or Playwright MCP
3. **Headful/Headless Mode**: Visual browser or background execution
4. **Screenshot & PDF Generation**: Capture outputs automatically
5. **Credential Management**: Secure storage for login credentials
6. **History Tracking**: Review past automations

### Advanced Features
1. **State Persistence**: Maintain browser state across sessions
2. **Cookie Management**: Handle authentication and session cookies

## File Structure
```
.
├── app/
│   ├── engines/           # Automation engines
│   ├── middleware/        # Security middleware
│   ├── routes/           # API routes
│   ├── services/         # Business logic
│   ├── static/           # CSS/JS assets
│   ├── templates/        # HTML templates
│   └── utils/            # Helper utilities
├── auth/                 # OAuth handling
├── config/               # Configuration files
├── integrations/         # Node.js Playwright MCP
├── main.py              # Application entry point
└── requirements.txt     # Python dependencies
```

## Recent Changes
- **2025-11-03**: Removed all learning features (Teaching Mode, Recall Mode, Task Library, Website Knowledge Base)
  - Deleted website learning utilities and prompt enhancer
  - Removed WebsiteKnowledgeBase database model
  - Removed learning-related routes and templates
  - Cleaned up navigation to remove learning features
  - Application now focuses on direct automation execution without learning overhead
- **2025-11-03**: Imported from GitHub and configured for Replit
  - Installed Python 3.11 and Node.js 20
  - Installed all Python dependencies
  - Installed Playwright browsers and system dependencies
  - Created .env file with privacy-focused defaults
  - Configured workflow to run on port 5000
  - Verified frontend is working correctly

## Development Notes

### System Dependencies
The following system packages were installed for Playwright browser support:
- X11 libraries (libxcb, libX11, libXcomposite, etc.)
- Graphics libraries (mesa, cairo, pango)
- Audio support (alsa-lib)
- Desktop integration (atk, at-spi2-atk, dbus)

### Known Limitations
1. **OAuth Required for AI**: Without OAuth credentials, automation features won't work
2. **Development Server**: Currently using Flask development server
3. **SQLite Database**: Suitable for development; consider PostgreSQL for production scale

## User Preferences
None set yet. This section will be updated as preferences are configured.
