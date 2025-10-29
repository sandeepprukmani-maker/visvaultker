# AI Browser Automation Platform

## Overview
An AI-powered browser automation web application that enables users to automate web tasks using natural language instructions. Built with Flask (Python) and Playwright, this application provides a comprehensive platform for creating, executing, and managing browser automation scripts.

**Last Updated:** October 29, 2025

## Recent Changes (October 29, 2025)

### UI/UX Improvements for Engine Selection
- ✅ **Browser-Use Engine**: Script panels completely hidden during execution
  - No code generation occurs for Browser-Use (direct execution only)
  - Cleaner, focused interface showing only automation prompt, logs, and screenshots
  - Faster execution without code generation overhead

- ✅ **Playwright MCP Engine**: Smart script panel display
  - Generated Script panel always visible (shows complete, working Playwright code)
  - Healed Script panel only shown when healing actually occurs
  - Prevents empty/placeholder panels from cluttering the UI
  - Accurate code generation using Playwright agents (no guessing locators)

### Execution History Enhancements
- ✅ **Complete Execution Details**: Each history entry includes:
  - Generated Script (the initially generated working code)
  - Healed Script (displayed only if healing occurred)
  - Prompt Used (the original automation instruction)
  - Screenshots (captured during execution)
  - Execution Logs (detailed steps, timestamps, and errors)

- ✅ **Re-execution with Auto-Healing**: 
  - Execute button in history details triggers re-execution
  - If script fails, Healer automatically intervenes
  - Fixed code displayed under Healed Script section
  - Fully functional, verified scripts after healing

### Enhanced Logging System
- ✅ **Browser-Use Engine**: Implemented concise, step-based logging with real-time output
  - Step-by-step action logs (Navigate, Click, Fill, etc.)
  - Automatic screenshot after last step (skips if user mentions "screenshot", "capture", or "snap")
  - Clear completion status (✅ Success / ❌ Failed)
  - Improved error messages with detailed failure reasons

- ✅ **Playwright MCP Engine**: Upgraded logging for better visibility
  - Step-based logging with human-readable action descriptions
  - Helper function for formatting browser actions
  - Completion status banners for success/failure scenarios
  - Cleaner error reporting with reduced verbosity

### Verification & Validation Enforcement
- ✅ **Both Engines**: Intelligent verification failure detection and reporting
  - Detects verification keywords in prompts (verify, check, ensure, validate, assert, confirm, etc.)
  - Enhanced system prompts instruct LLM to explicitly report verification pass/fail
  - Automatic failure detection when verifications don't pass
  - Clear error logging with "❌ VERIFICATION FAILED" banner
  - Detailed error messages showing:
    * Original instruction with verification requirement
    * Specific reason for verification failure
    * Number of steps completed before failure
  - Returns `success: false` with `error_type: "VerificationError"` for failed verifications
  - Avoids false positives by checking for explicit success indicators first
  - Example: "verify search button exists" will fail with clear message if button not found

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
  - Browser-use library (0.9.1)
  - Playwright (1.55.0)
  - Playwright MCP Server (Node.js component)

### Frontend
- Pure JavaScript (no framework)
- Dark theme UI with responsive design
- Real-time automation dashboard
- Located in `app/templates/` and `app/static/`

### Key Components

#### Core Services
1. **Engine Orchestrator** (`app/services/engine_orchestrator.py`) - Manages automation engines with dual workflow support
2. **Browser Use Engine** (`app/engines/browser_use/`) - Optimized browser automation
3. **Playwright MCP** (`app/engines/playwright_mcp/`) - Model Context Protocol integration

#### Enhanced Workflow Services (VisionVault)
4. **Intelligent Validator** (`app/services/intelligent_validator.py`) - Web scraping and element verification with confidence scoring
5. **Enhanced Prompt Generator** (`app/services/enhanced_prompt_generator.py`) - Generates detailed prompts with accurate element locators
6. **AI Script Generator** (`app/services/ai_script_generator.py`) - Creates clean scripts using multiple LLM providers (Anthropic, OpenAI, Groq)
7. **Dynamic Healer** (`app/services/dynamic_healer.py`) - Automatically detects and resolves execution issues in real-time

#### Legacy Agents (Fallback)
8. **Agents** (`app/agents/`) - Planner, Generator, Healer, Orchestrator (used when enhanced workflow is disabled or fails)

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
│   ├── agents/            # AI agents (planner, generator, healer, orchestrator)
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
├── automation_scripts/   # Generated automation scripts
├── tests/               # Test files
├── main.py              # Application entry point
└── requirements.txt     # Python dependencies
```

## Available Pages

1. **Dashboard** (`/`) - Main automation interface
2. **Configuration** (`/configuration`) - Settings and preferences
3. **History** (`/history`) - Execution history
4. **Task Library** (`/task-library`) - Saved tasks
5. **Teaching Mode** (`/teaching-mode`) - Interactive teaching
6. **Recall Mode** (`/recall-mode`) - Memory recall features

## API Endpoints

- `GET /health` - Health check endpoint
- `GET /api/mcp/status` - MCP server status
- `POST /api/mcp/restart` - Restart MCP server
- Additional automation endpoints in `app/routes/api.py`

## Database

**Database:** SQLite (`automation_history.db`)

**Models:**
- `ExecutionHistory` - Stores automation execution records with prompts, results, scripts, screenshots, and performance metrics

## Development Notes

### Performance Optimization
The application is configured for **balanced fast mode**:
- Page load times: 0.3-0.6s
- Action wait times: 0.2s
- See `docs/PERFORMANCE_GUIDE.md` for tuning options

### Privacy & Security
- Telemetry and cloud sync are **disabled by default**
- All data stays local/in your database
- Cache-Control headers prevent browser caching issues
- Session secrets should be set for production

### MCP Server
The Playwright MCP server runs in Node.js and provides:
- Browser automation via Model Context Protocol
- Persistent mode for faster responses
- Automatic restart on failure
- Clean shutdown on app exit

## Troubleshooting

**App won't start:**
- Check the workflow logs for errors
- Ensure Python dependencies are installed
- Verify Playwright browsers are installed

**AI features not working:**
- This is expected without OAuth credentials
- Add the required OAuth environment variables to use AI features

**Database issues:**
- SQLite is used by default and should work out of the box
- Check file permissions on `automation_history.db`

**Slow automation:**
- Adjust settings in `config/config.ini` per `docs/PERFORMANCE_GUIDE.md`
- Check MCP server status at `/api/mcp/status`

## Next Steps

1. **Optional:** Add OAuth credentials via Replit Secrets to enable AI features
2. Explore the web interface at the preview URL
3. Review the configuration in `config/config.ini`
4. Check out the documentation in the `docs/` directory

## Deployment

The application is ready for deployment on Replit. It will run in development mode by default. For production deployment:

1. Set `SESSION_SECRET` environment variable
2. Configure OAuth credentials for AI features
3. The app is already configured to run on port 5000 with proper host settings (0.0.0.0)

## Technical Stack

- **Python:** 3.11
- **Node.js:** 20
- **Web Framework:** Flask 3.1.2
- **Database:** SQLAlchemy 2.0.44
- **Browser Automation:** Playwright 1.55.0, browser-use 0.9.1
- **AI Integration:** Anthropic, OpenAI, Google GenAI, Groq
- **Testing:** Playwright Test Agents (Planner, Generator, Healer)
