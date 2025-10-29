# AI Browser Automation Platform

## Overview
An AI-powered browser automation web application that enables users to automate web tasks using natural language instructions. Built with Flask (Python) and Playwright, this application provides a comprehensive platform for creating, executing, and managing browser automation scripts.

**Last Updated:** October 28, 2025

## Project Status
✅ **Fully configured and running on Replit**

- Flask web server running on port 5000
- SQLite database initialized for local development
- Playwright browsers installed (Chromium)
- Privacy settings configured (telemetry disabled)
- All dependencies installed

## Architecture

### Backend (Python/Flask)
- **Framework:** Flask 3.1.2 with Flask-SQLAlchemy
- **Database:** SQLite (development) with PostgreSQL support via `DATABASE_URL`
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
1. **Engine Orchestrator** (`app/services/engine_orchestrator.py`) - Manages automation engines
2. **Browser Use Engine** (`app/engines/browser_use/`) - Optimized browser automation
3. **Playwright MCP** (`app/engines/playwright_mcp/`) - Model Context Protocol integration
4. **Agents** (`app/agents/`) - Planner, Generator, Healer, Orchestrator

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
- `DATABASE_URL` - PostgreSQL connection string (optional, uses SQLite if not set)

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

**Current:** SQLite (`automation_history.db`)

**Models:**
- `ExecutionHistory` - Stores automation execution records with prompts, results, scripts, screenshots, and performance metrics

**To use PostgreSQL:**
1. Create a Replit PostgreSQL database
2. The `DATABASE_URL` environment variable will be automatically set
3. Restart the application

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
2. **Optional:** Create a PostgreSQL database for production use
3. Explore the web interface at the preview URL
4. Review the configuration in `config/config.ini`
5. Check out the documentation in the `docs/` directory

## Deployment

The application is ready for deployment on Replit. It will run in development mode by default. For production deployment:

1. Set `SESSION_SECRET` environment variable
2. Consider using PostgreSQL instead of SQLite
3. Configure OAuth credentials for AI features
4. The app is already configured to run on port 5000 with proper host settings (0.0.0.0)

## Technical Stack

- **Python:** 3.11
- **Node.js:** 20
- **Web Framework:** Flask 3.1.2
- **Database:** SQLAlchemy 2.0.44
- **Browser Automation:** Playwright 1.55.0, browser-use 0.9.1
- **AI Integration:** Anthropic, OpenAI, Google GenAI, Groq
- **Testing:** Playwright Test Agents (Planner, Generator, Healer)
