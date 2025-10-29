# AI Browser Automation Platform

## Overview
An AI-powered browser automation web application that enables users to automate web tasks using natural language instructions. Built with Flask (Python) and Playwright, this application provides a comprehensive platform for executing and managing browser automation tasks.

**Last Updated:** October 29, 2025

## Recent Changes (October 29, 2025)

### Three-Agent Python Code Generation System (Latest)
- ✅ **Playwright MCP Engine**: Implemented intelligent Python script generation
  - **StrictModeLocatorEngine**: Multi-strategy locator generation with priority chain:
    - data-testid attributes (highest priority)
    - ARIA roles and accessible names
    - Unique element attributes (id, name, etc.)
    - Text content matching
    - CSS selectors with filters (fallback)
  - **PlannerAgent**: Interactive app exploration and structured YAML plan generation
    - Validates locators during exploration
    - Generates step-by-step automation plans
    - Ensures robust element detection
  - **GeneratorAgent**: Production-ready Python Playwright code synthesis
    - Async/await pattern with proper error handling
    - Retry logic and timeout management
    - Clean, readable, standalone executable scripts
  - **HealerAgent**: Automatic script patching and error recovery
    - Analyzes Playwright trace files for failures
    - Identifies broken locators and actions
    - Patches code with improved strategies
  - **Database Models**: Extended schema for plan/script/trace persistence
    - AutomationPlan table stores YAML plans
    - GeneratedScript table stores Python code with versioning
    - TraceFile table stores execution traces for analysis
  - **UI Integration**: Generated Python scripts display in "Generated Script" panel

### Intelligent Dropdown Handling
- ✅ **Both Engines Enhanced**: Added intelligent dropdown list handling
  - Native HTML `<select>` element support
  - Custom JavaScript dropdowns (Material-UI, Ant Design, etc.)
  - Long dropdown lists with scrolling
  - Dropdowns with search/filter capabilities
  - Multi-select dropdown support
  - Comprehensive troubleshooting strategies

### UI/UX Improvements for Engine Selection
- ✅ **Browser-Use Engine**: Direct execution with real-time feedback
  - Clean interface showing automation prompt, logs, and screenshots
  - Fast execution without code generation overhead

- ✅ **Playwright MCP Engine**: Direct browser automation
  - Real-time execution logs
  - Screenshot capture during automation

### Execution History Enhancements
- ✅ **Complete Execution Details**: Each history entry includes:
  - Prompt Used (the original automation instruction)
  - Screenshots (captured during execution)
  - Execution Logs (detailed steps, timestamps, and errors)
  - Success/failure status

### Enhanced Logging System
- ✅ **Browser-Use Engine**: Implemented concise, step-based logging with real-time output
  - Step-by-step action logs (Navigate, Click, Fill, etc.)
  - Automatic screenshot after last step
  - Clear completion status (✅ Success / ❌ Failed)
  - Improved error messages with detailed failure reasons

- ✅ **Playwright MCP Engine**: Upgraded logging for better visibility
  - Step-based logging with human-readable action descriptions
  - Completion status banners for success/failure scenarios
  - Cleaner error reporting with reduced verbosity

### Verification & Validation Enforcement
- ✅ **Both Engines**: Intelligent verification failure detection and reporting
  - Detects verification keywords in prompts (verify, check, ensure, validate, assert, confirm, etc.)
  - Enhanced system prompts instruct LLM to explicitly report verification pass/fail
  - Automatic failure detection when verifications don't pass
  - Clear error logging with "❌ VERIFICATION FAILED" banner
  - Returns `success: false` with `error_type: "VerificationError"` for failed verifications

## Project Status
✅ **Fully configured and running on Replit**

- Flask web server running on port 5000
- SQLite database initialized for local development
- Playwright browsers installed (Chromium)
- Privacy settings configured (telemetry disabled)
- All dependencies installed
- Enhanced logging system active in both automation engines

## Architecture

### Backend (Python/Flask)
- **Framework:** Flask 3.1.2 with Flask-SQLAlchemy
- **Database:** SQLite
- **Browser Automation:** 
  - Browser-use library (0.9.1) with intelligent dropdown handling
  - Playwright (1.55.0) with MCP integration
  - Playwright MCP Server (Node.js component)

### Intelligent Dropdown Handling
Both automation engines include enhanced dropdown interaction capabilities:

**Supported Dropdown Types:**
1. **Native HTML Select** - Standard `<select>` elements
2. **Custom JS Dropdowns** - Material-UI, Ant Design, Bootstrap, etc.
3. **Searchable Dropdowns** - Dropdowns with filter/search functionality
4. **Long Lists** - Automatic scrolling for dropdowns with many options
5. **Multi-Select** - Support for selecting multiple options

**Smart Features:**
- Automatic detection of dropdown type
- Intelligent waiting for dynamic content
- Scroll-into-view for hidden options
- Search/filter utilization when available
- Comprehensive error handling and recovery

### Frontend
- Pure JavaScript (no framework)
- Dark theme UI with responsive design
- Real-time automation dashboard
- Located in `app/templates/` and `app/static/`

### Key Components

#### Core Services
1. **Engine Orchestrator** (`app/services/engine_orchestrator.py`) - Manages automation engines
2. **Browser Use Engine** (`app/engines/browser_use/`) - Optimized browser automation
3. **Playwright MCP** (`app/engines/playwright_mcp/`) - Model Context Protocol integration

## Configuration

### Environment Variables
The application uses these environment variables (all optional for basic functionality):

**OAuth Configuration (for AI features):**
- `OAUTH_TOKEN_URL` - OAuth provider token endpoint
- `OAUTH_CLIENT_ID` - OAuth client ID
- `OAUTH_CLIENT_SECRET` - OAuth client secret
- `OAUTH_GRANT_TYPE` - Grant type (default: client_credentials)
- `OAUTH_SCOPE` - Required OAuth scope
- `GW_BASE_URL` - Gateway API endpoint

**Database:**
- SQLite database file: `automation_history.db`

**Security:**
- `SESSION_SECRET` - Flask session secret (auto-generated if not set)
- `CORS_ALLOWED_ORIGINS` - CORS allowed origins (default: *)

**Privacy:**
- `ANONYMIZED_TELEMETRY=false` - Disables telemetry (already set)
- `BROWSER_USE_CLOUD_SYNC=false` - Disables cloud sync (already set)

### Application Settings
Configuration is managed in `config/config.ini`:

- **Browser Performance:** Optimized wait times for balanced speed/reliability
- **MCP Server Mode:** `always_run` (persistent server for faster response)
- **Max Steps:** 60 (maximum automation steps)
- **Retry Mechanism:** 2 retries with exponential backoff
- **Advanced Features:** Screenshots, PDFs, cookie management, state persistence

## Running Without OAuth

The application **will run without OAuth credentials**. You'll see a warning in the logs, but:
- The web interface will be accessible
- You can view the dashboard and UI
- Actual AI automation features will not work until OAuth is configured

To use AI features, you'll need to add the OAuth credentials using Replit Secrets.

## Project Structure

```
.
├── app/                    # Main application package
│   ├── engines/           # Automation engines
│   │   ├── browser_use/   # Browser-use engine with optimizations
│   │   └── playwright_mcp/# Playwright MCP server integration
│   ├── routes/            # API routes
│   ├── services/          # Business logic services
│   ├── static/            # Static assets (CSS, JS)
│   ├── templates/         # HTML templates
│   ├── utils/             # Utility functions
│   └── models.py          # SQLAlchemy database models
├── integrations/          # External integrations
│   └── playwright_mcp_node/  # Node.js Playwright MCP server
├── config/               # Configuration files
│   └── config.ini       # Application configuration
├── docs/                 # Documentation
├── main.py              # Application entry point
└── requirements.txt     # Python dependencies
```

## Available Pages

1. **Dashboard** (`/`) - Main automation interface
2. **History** (`/history`) - Execution history and logs
3. **Configuration** (`/configuration`) - Engine and settings management
4. **Teaching Mode** (`/teaching-mode`) - Interactive automation learning
5. **Task Library** (`/task-library`) - Saved automation tasks
6. **Recall Mode** (`/recall-mode`) - Replay previous automations

## API Endpoints

### Automation Execution
- `POST /api/execute` - Execute automation instruction
  - Body: `{ "instruction": "...", "engine": "browser_use|playwright_mcp", "headless": true|false }`

### History Management
- `GET /api/history` - Get execution history (paginated)
- `GET /api/history/<id>` - Get specific history item
- `POST /api/history/<id>/execute` - Re-execute from history
- `DELETE /api/history` - Delete all history
- `DELETE /api/history/<id>` - Delete specific history item

### Engine Management
- `POST /api/engines/cleanup` - Clean up engine resources
- `GET /api/engines/status` - Get engine status

### System
- `GET /api/health` - Health check endpoint

## Tech Stack

**Backend:**
- Python 3.11
- Flask 3.1.2
- SQLAlchemy 2.0.44
- Playwright 1.55.0
- browser-use 0.9.1

**Frontend:**
- Vanilla JavaScript
- Dark theme CSS
- Responsive design

**Database:**
- SQLite (development)
- Supports PostgreSQL (production)

**AI/LLM:**
- OpenAI GPT-4.1
- Support for Anthropic Claude
- Support for Google Gemini
- Support for Groq

## Development

### Local Setup
The project is already configured and running on Replit. No additional setup needed!

### Database
- Uses SQLite for development
- Database file: `automation_history.db`
- Models defined in `app/models.py`

### Logging
- Detailed logging in `app/utils/logging_config.py`
- Configurable log levels in `config/config.ini`
- Real-time execution logs in the UI

## Privacy & Security

- ✅ **Telemetry Disabled** - No data sent to external services
- ✅ **Cloud Sync Disabled** - All data stays local
- ✅ **Session Security** - Secure session management
- ✅ **CORS Configuration** - Controlled cross-origin requests
- ✅ **OAuth Support** - Secure API authentication

## Performance

### Optimizations
- Fast browser automation with optimized wait times
- Persistent MCP server for reduced latency
- Retry mechanism for reliability
- Efficient screenshot capture
- Database query optimization

### Monitoring
- Execution time tracking
- Step count tracking
- Success/failure metrics
- Error logging and analysis

## Troubleshooting

### Common Issues

**AI features not working:**
- Check OAuth credentials are set in Replit Secrets
- Verify GW_BASE_URL is correct
- Check logs for authentication errors

**Browser automation fails:**
- Check if Playwright browsers are installed
- Verify headless mode setting
- Review execution logs for specific errors

**Database errors:**
- Check `automation_history.db` file exists
- Verify write permissions
- Review database logs

## Future Enhancements

Potential areas for improvement:
- Additional automation engines
- Enhanced screenshot capabilities
- Advanced element detection
- Custom automation workflows
- API rate limiting improvements

## Support

For issues or questions:
1. Check the execution logs
2. Review this documentation
3. Examine the console output
4. Check Replit environment status

---

**Last Updated:** October 29, 2025
